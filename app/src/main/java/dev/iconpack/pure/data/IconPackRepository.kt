package dev.iconpack.pure.data

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import dev.iconpack.pure.R
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.xmlpull.v1.XmlPullParser
import java.util.Locale

class IconPackRepository(private val context: Context) {

    // Fast O(1) reflection lookup inspired by Lawnicons (avoids 4,200 slow getIdentifier calls)
    private val drawableIdMap: Map<String, Int> by lazy {
        try {
            R.drawable::class.java.fields.associate { field ->
                field.name to field.getInt(null)
            }
        } catch (_: Exception) {
            emptyMap()
        }
    }

    private data class MetaEntry(
        val primaryLabel: String,
        val keywords: String
    )

    private val metadataByDrawable: Map<String, MetaEntry> by lazy {
        loadOfflineMetadata()
    }

    private val installedLabelsByPackage: Map<String, String> by lazy {
        queryInstalledPackageLabels()
    }

    private val replacerRules: List<Pair<String, String>> by lazy {
        context.resources.getStringArray(R.array.icon_name_replacer).mapNotNull { entry ->
            val idx = entry.indexOf(',')
            if (idx <= 0) null else entry.substring(0, idx) to entry.substring(idx + 1)
        }
    }

    private data class AliasEntry(
        val zhTitle: String,
        val enTitle: String,
        val extraKeywords: String
    )

    private val aliasByDrawable: Map<String, AliasEntry> by lazy {
        context.resources.getStringArray(R.array.icon_search_aliases).mapNotNull { line ->
            val parts = line.split('|').map { it.trim() }.filter { it.isNotEmpty() }
            if (parts.size < 3) null
            else parts[0] to AliasEntry(
                zhTitle = parts[1],
                enTitle = parts.firstOrNull { p -> p.all { it.code < 128 } && p != parts[0] && !p.contains('.') } ?: parts[1],
                extraKeywords = parts.drop(1).joinToString(" | ")
            )
        }.toMap()
    }

    @SuppressLint("DiscouragedApi")
    fun resolveDrawableId(name: String): Int {
        return drawableIdMap[name]
            ?: context.resources.getIdentifier(name, "drawable", context.packageName)
    }

    fun createPreviewItem(name: String): IconItem? {
        val id = resolveDrawableId(name)
        if (id == 0) return null
        return IconItem(
            drawableName = name,
            displayName = beautifyDrawableName(name),
            resId = id
        )
    }

    suspend fun loadIconCategories(): Pair<List<IconCategory>, Int> = withContext(Dispatchers.IO) {
        val metaMap = metadataByDrawable
        val installedLabels = installedLabelsByPackage
        val categories = mutableListOf<IconCategory>()
        val uniqueResIds = HashSet<Int>(4500)
        val itemCache = HashMap<String, IconItem>(4500)
        val res = context.resources
        val parser = res.getXml(R.xml.drawable)

        var currentTitle: String? = null
        var currentRawId: String? = null
        var currentList = mutableListOf<IconItem>()

        fun flushCategory() {
            val title = currentTitle
            val rawId = currentRawId
            if (title != null && rawId != null && currentList.isNotEmpty()) {
                categories.add(IconCategory(id = rawId, title = title, icons = currentList.toList()))
            }
        }

        try {
            var event = parser.eventType
            while (event != XmlPullParser.END_DOCUMENT) {
                if (event == XmlPullParser.START_TAG) {
                    when (parser.name) {
                        "category" -> {
                            flushCategory()
                            val titleResId = parser.getAttributeResourceValue(null, "title", 0)
                            val rawTitle = parser.getAttributeValue(null, "title").orEmpty()
                            currentRawId = if (titleResId != 0) res.getResourceEntryName(titleResId) else rawTitle
                            currentTitle = if (titleResId != 0) {
                                context.getString(titleResId)
                            } else {
                                resolveCategoryTitle(rawTitle)
                            }
                            currentList = mutableListOf()
                        }
                        "item" -> {
                            val drawableName = parser.getAttributeValue(null, "drawable").orEmpty()
                            if (drawableName.isNotEmpty()) {
                                val cached = itemCache[drawableName]
                                if (cached != null) {
                                    currentList.add(cached)
                                } else {
                                    val resId = resolveDrawableId(drawableName)
                                    if (resId != 0) {
                                        uniqueResIds.add(resId)
                                        val built = buildIconItem(drawableName, resId, metaMap, installedLabels)
                                        itemCache[drawableName] = built
                                        currentList.add(built)
                                    }
                                }
                            }
                        }
                    }
                }
                event = parser.next()
            }
            flushCategory()
        } finally {
            parser.close()
        }

        categories to uniqueResIds.size
    }

    suspend fun getMappedComponents(drawableName: String): List<MappedComponentInfo> = withContext(Dispatchers.IO) {
        val installedLabels = installedLabelsByPackage
        val metaPrimary = metadataByDrawable[drawableName]?.primaryLabel.orEmpty()
        val results = mutableListOf<MappedComponentInfo>()
        val seen = HashSet<String>()
        val parser = context.resources.getXml(R.xml.appfilter)

        try {
            var event = parser.eventType
            while (event != XmlPullParser.END_DOCUMENT) {
                if (event == XmlPullParser.START_TAG && parser.name == "item") {
                    val dr = parser.getAttributeValue(null, "drawable").orEmpty()
                    if (dr == drawableName) {
                        val comp = parser.getAttributeValue(null, "component").orEmpty().trim()
                        if (comp.startsWith("ComponentInfo{") && comp.endsWith("}") && seen.add(comp)) {
                            val inner = comp.substring("ComponentInfo{".length, comp.length - 1)
                            val pkg = inner.substringBefore('/')
                            val liveLabel = installedLabels[pkg]
                            val label = liveLabel ?: metaPrimary.ifBlank { pkg }
                            results.add(
                                MappedComponentInfo(
                                    appLabel = label,
                                    packageName = pkg,
                                    componentInfo = comp,
                                    isInstalled = liveLabel != null
                                )
                            )
                        }
                    }
                }
                event = parser.next()
            }
        } finally {
            parser.close()
        }

        results.sortedWith(
            compareByDescending<MappedComponentInfo> { it.isInstalled }
                .thenBy { it.packageName }
                .thenBy { it.componentInfo }
        )
    }

    suspend fun scanInstalledAppsStats(): InstalledAppsStats = withContext(Dispatchers.IO) {
        val themedComponents = loadThemedComponentSet()
        val pm = context.packageManager
        val mainIntent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val resolveInfos = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.queryIntentActivities(mainIntent, PackageManager.ResolveInfoFlags.of(0L))
        } else {
            @Suppress("DEPRECATION")
            pm.queryIntentActivities(mainIntent, 0)
        }

        val selfPkg = context.packageName
        var total = 0
        var themed = 0
        val seenComponents = HashSet<String>()

        for (ri in resolveInfos) {
            val ai = ri.activityInfo ?: continue
            if (ai.packageName == selfPkg) continue
            val comp = "ComponentInfo{${ai.packageName}/${ai.name}}"
            if (!seenComponents.add(comp)) continue
            total++
            if (comp in themedComponents) {
                themed++
            }
        }

        InstalledAppsStats(
            totalInstalled = total,
            themedCount = themed
        )
    }

    private fun buildIconItem(
        drawableName: String,
        resId: Int,
        metaMap: Map<String, MetaEntry>,
        installedLabels: Map<String, String>
    ): IconItem {
        val variantMatch = VARIANT_SUFFIX_RE.matchEntire(drawableName)
        val baseDrawable = variantMatch?.groupValues?.get(1) ?: drawableName
        val variantNum = variantMatch?.groupValues?.get(2)

        val meta = metaMap[drawableName] ?: metaMap[baseDrawable]
        val alias = aliasByDrawable[drawableName] ?: aliasByDrawable[baseDrawable]
        val keywords = buildString {
            if (!meta?.keywords.isNullOrEmpty()) append(meta!!.keywords)
            if (alias != null) {
                if (isNotEmpty()) append(" | ")
                append(alias.extraKeywords)
            }
        }

        // Find if any mapped package in keywords is currently installed on device to get localized Chinese/system title
        var liveInstalledTitle: String? = null
        if (keywords.isNotEmpty()) {
            for (token in keywords.split('|')) {
                val t = token.trim()
                val hit = installedLabels[t]
                if (hit != null) {
                    liveInstalledTitle = hit
                    break
                }
            }
        }

        val isZhLocale = Locale.getDefault().language.startsWith("zh", ignoreCase = true)
        val cleanMetaLabel = meta?.primaryLabel
            ?.substringBefore("~~")
            ?.trim()
            .orEmpty()

        val baseTitle = when {
            !liveInstalledTitle.isNullOrBlank() -> liveInstalledTitle
            alias != null -> if (isZhLocale) alias.zhTitle else alias.enTitle
            cleanMetaLabel.isNotEmpty() -> cleanMetaLabel
            else -> beautifyDrawableName(baseDrawable)
        }
        val displayName = if (variantNum != null && !baseTitle.endsWith("($variantNum)")) {
            "$baseTitle ($variantNum)"
        } else {
            baseTitle
        }

        val searchBlob = buildString {
            append(drawableName)
            append(' ')
            append(displayName)
            if (keywords.isNotEmpty()) {
                append(' ')
                append(keywords)
            }
            if (!liveInstalledTitle.isNullOrBlank()) {
                append(' ')
                append(liveInstalledTitle)
            }
        }.lowercase(Locale.ROOT)

        return IconItem(
            drawableName = drawableName,
            displayName = displayName,
            resId = resId,
            searchBlob = searchBlob
        )
    }

    private fun loadOfflineMetadata(): Map<String, MetaEntry> {
        val map = HashMap<String, MetaEntry>(4200)
        val parser = context.resources.getXml(R.xml.icon_metadata)
        try {
            var event = parser.eventType
            while (event != XmlPullParser.END_DOCUMENT) {
                if (event == XmlPullParser.START_TAG && parser.name == "icon") {
                    val dr = parser.getAttributeValue(null, "drawable").orEmpty()
                    if (dr.isNotEmpty()) {
                        val label = parser.getAttributeValue(null, "label").orEmpty()
                        val kw = parser.getAttributeValue(null, "keywords").orEmpty()
                        val entry = MetaEntry(label, kw)
                        map[dr] = entry
                        val base = VARIANT_SUFFIX_RE.matchEntire(dr)?.groupValues?.get(1)
                        if (base != null && base !in map) {
                            map[base] = entry
                        }
                    }
                }
                event = parser.next()
            }
        } finally {
            parser.close()
        }
        return map
    }

    private fun queryInstalledPackageLabels(): Map<String, String> {
        val map = HashMap<String, String>(128)
        val pm = context.packageManager
        val mainIntent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)
        val resolveInfos = try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.queryIntentActivities(mainIntent, PackageManager.ResolveInfoFlags.of(0L))
            } else {
                @Suppress("DEPRECATION")
                pm.queryIntentActivities(mainIntent, 0)
            }
        } catch (_: Exception) {
            emptyList()
        }
        for (ri in resolveInfos) {
            val pkg = ri.activityInfo?.packageName ?: continue
            if (pkg !in map) {
                val label = ri.loadLabel(pm)?.toString()?.trim()
                if (!label.isNullOrEmpty()) {
                    map[pkg] = label
                }
            }
        }
        return map
    }

    private fun loadThemedComponentSet(): Set<String> {
        val set = HashSet<String>(9200)
        val parser = context.resources.getXml(R.xml.appfilter)
        try {
            var event = parser.eventType
            while (event != XmlPullParser.END_DOCUMENT) {
                if (event == XmlPullParser.START_TAG && (parser.name == "item" || parser.name == "calendar")) {
                    val comp = parser.getAttributeValue(null, "component")
                    if (!comp.isNullOrBlank()) {
                        set.add(comp.trim())
                    }
                }
                event = parser.next()
            }
        } finally {
            parser.close()
        }
        return set
    }

    @SuppressLint("DiscouragedApi")
    private fun resolveCategoryTitle(rawTitle: String): String {
        if (rawTitle.startsWith("@string/")) {
            val strName = rawTitle.removePrefix("@string/")
            val strId = context.resources.getIdentifier(strName, "string", context.packageName)
            if (strId != 0) return context.getString(strId)
        } else if (rawTitle.startsWith("@")) {
            val numericId = rawTitle.removePrefix("@").toIntOrNull()
            if (numericId != null && numericId != 0) {
                return runCatching { context.getString(numericId) }.getOrDefault(rawTitle)
            }
        }
        val strId = context.resources.getIdentifier(rawTitle, "string", context.packageName)
        return if (strId != 0) context.getString(strId) else rawTitle
    }

    private fun beautifyDrawableName(raw: String): String {
        var working = raw
        for ((from, to) in replacerRules) {
            if (to.isEmpty() && working.startsWith(from)) {
                working = working.removePrefix(from)
            } else if (working == from) {
                return to
            } else if (from.endsWith("_") && working.startsWith(from)) {
                working = to + working.removePrefix(from)
            }
        }
        working = working.replace("_alt", "")
        return working
            .split('_')
            .filter { it.isNotEmpty() }
            .joinToString(" ") { part ->
                part.replaceFirstChar { ch ->
                    if (ch.isLowerCase()) ch.titlecase(Locale.getDefault()) else ch.toString()
                }
            }
    }

    companion object {
        private val VARIANT_SUFFIX_RE = Regex("^(.+?)(?:_alt)?_(\\d+)$")
    }
}
