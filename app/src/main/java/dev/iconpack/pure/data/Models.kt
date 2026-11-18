package dev.iconpack.pure.data

data class IconItem(
    val drawableName: String,
    val displayName: String,
    val resId: Int,
    val searchBlob: String = "$drawableName $displayName".lowercase()
)

data class IconCategory(
    val id: String,
    val title: String,
    val icons: List<IconItem>
)

data class MappedComponentInfo(
    val appLabel: String,
    val packageName: String,
    val componentInfo: String,
    val isInstalled: Boolean
)

data class LauncherEntry(
    val key: String,
    val name: String,
    val packageNames: List<String>,
    val isInstalled: Boolean,
    val isDefault: Boolean,
    val supportsDirectApply: Boolean
)

data class InstalledAppsStats(
    val totalInstalled: Int,
    val themedCount: Int
)
