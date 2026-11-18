package dev.iconpack.pure.util

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.widget.Toast
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import dev.iconpack.pure.R
import dev.iconpack.pure.data.LauncherEntry

object LauncherHelper {

    private data class Spec(
        val key: String,
        val name: String,
        val packages: List<String>,
        val directApply: Boolean = true
    )

    private val SPECS = listOf(
        Spec("nova", "Nova Launcher", listOf("com.teslacoilsw.launcher", "com.teslacoilsw.launcher.prime")),
        Spec("lawnchair", "Lawnchair", listOf("app.lawnchair", "app.lawnchair.play", "ch.deletescape.lawnchair.plah", "ch.deletescape.lawnchair.ci", "ch.deletescape.lawnchair")),
        Spec("niagara", "Niagara Launcher", listOf("bitpit.launcher")),
        Spec("smart", "Smart Launcher", listOf("ginlemon.flowerfree")),
        Spec("smartpro", "Smart Launcher Pro", listOf("ginlemon.flowerpro", "ginlemon.flowerpro.special")),
        Spec("action", "Action Launcher", listOf("com.actionlauncher.playstore", "com.chrislacy.actionlauncher.pro")),
        Spec("apex", "Apex Launcher", listOf("com.anddoes.launcher", "com.anddoes.launcher.pro")),
        Spec("adw", "ADW Launcher", listOf("org.adw.launcher")),
        Spec("adwex", "ADW EX Launcher", listOf("org.adwfreak.launcher")),
        Spec("aio", "AIO Launcher", listOf("ru.execbit.aiolauncher")),
        Spec("atom", "Atom Launcher", listOf("com.dlto.atom.launcher"), directApply = false),
        Spec("gip", "Global Icon Pack", listOf("com.richardluo.globalIconPack")),
        Spec("go", "GO Launcher EX", listOf("com.gau.go.launcherex")),
        Spec("googlenow", "Google Now Launcher", listOf("com.google.android.launcher"), directApply = false),
        Spec("holo", "Holo Launcher", listOf("com.mobint.hololauncher")),
        Spec("holoics", "Holo Launcher HD", listOf("com.mobint.hololauncher.hd")),
        Spec("lg", "LG Home", listOf("com.lge.launcher2", "com.lge.launcher3"), directApply = false),
        Spec("lineageos", "LineageOS Trebuchet", listOf("org.lineageos.trebuchet", "com.android.launcher3"), directApply = false),
        Spec("lucid", "Lucid Launcher", listOf("com.powerpoint45.launcher", "com.powerpoint45.launcherpro")),
        Spec("moto", "Moto Launcher", listOf("com.motorola.launcher3"), directApply = false),
        Spec("nothing", "Nothing Launcher", listOf("com.nothing.launcher"), directApply = false),
        Spec("oneplus", "OnePlus / ColorOS Launcher", listOf("net.oneplus.launcher", "com.android.launcher"), directApply = false),
        Spec("pixel", "Pixel Launcher", listOf("com.google.android.apps.nexuslauncher"), directApply = false),
        Spec("posidon", "Posidon Launcher", listOf("posidon.launcher")),
        Spec("projectivy", "Projectivy Launcher", listOf("com.spocky.projengmenu")),
        Spec("solo", "Solo Launcher", listOf("home.solo.launcher.free")),
        Spec("square", "Square Home", listOf("com.ss.squarehome2")),
        Spec("tsf", "TSF Launcher", listOf("com.tsf.shell"))
    )

    val supportedCount: Int
        get() = SPECS.size

    fun loadLaunchers(context: Context): List<LauncherEntry> {
        val pm = context.packageManager
        val defaultPkg = resolveDefaultHomePackage(pm)
        return SPECS.map { spec ->
            val installedPkg = spec.packages.firstOrNull { isPackageInstalled(pm, it) }
            LauncherEntry(
                key = spec.key,
                name = spec.name,
                packageNames = spec.packages,
                isInstalled = installedPkg != null,
                isDefault = installedPkg != null && spec.packages.contains(defaultPkg),
                supportsDirectApply = spec.directApply
            )
        }.sortedWith(
            compareByDescending<LauncherEntry> { it.isDefault }
                .thenByDescending { it.isInstalled }
                .thenBy { it.name }
        )
    }

    fun applyForDefaultOrSelected(context: Context, entry: LauncherEntry? = null) {
        val target = entry ?: loadLaunchers(context).firstOrNull { it.isDefault || it.isInstalled }
        if (target == null) {
            showManualDialog(context, context.getString(R.string.app_name))
            return
        }
        executeLauncherApply(context, target)
    }

    fun executeLauncherApply(context: Context, launcher: LauncherEntry) {
        if (!launcher.isInstalled) {
            Toast.makeText(
                context,
                context.getString(R.string.launcher_not_installed_toast, launcher.name),
                Toast.LENGTH_SHORT
            ).show()
            return
        }
        if (!launcher.supportsDirectApply) {
            showManualDialog(context, launcher.name)
            return
        }

        val pkg = context.packageName
        val appName = context.getString(R.string.app_name)
        val intent: Intent? = when (launcher.key) {
            "nova" -> Intent("com.teslacoilsw.launcher.APPLY_ICON_THEME").apply {
                setPackage("com.teslacoilsw.launcher")
                putExtra("com.teslacoilsw.launcher.extra.ICON_THEME_TYPE", "GO")
                putExtra("com.teslacoilsw.launcher.extra.ICON_THEME_PACKAGE", pkg)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            "lawnchair" -> Intent("ch.deletescape.lawnchair.APPLY_ICONS", null).apply {
                putExtra("packageName", pkg)
            }
            "niagara" -> Intent("bitpit.launcher.APPLY_ICONS").apply {
                setPackage("bitpit.launcher")
                putExtra("packageName", pkg)
            }
            "smart", "smartpro" -> Intent("ginlemon.smartlauncher.setGSLTHEME").apply {
                putExtra("package", pkg)
            }
            "action" -> context.packageManager.getLaunchIntentForPackage(
                launcher.packageNames.first { isPackageInstalled(context.packageManager, it) }
            )?.apply {
                putExtra("apply_icon_pack", pkg)
            }
            "apex" -> Intent("com.anddoes.launcher.SET_THEME").apply {
                putExtra("com.anddoes.launcher.THEME_PACKAGE_NAME", pkg)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            "adw" -> Intent("org.adw.launcher.SET_THEME").apply {
                putExtra("org.adw.launcher.theme.NAME", pkg)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            "adwex" -> Intent("org.adwfreak.launcher.SET_THEME").apply {
                putExtra("org.adwfreak.launcher.theme.NAME", pkg)
                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            }
            "aio" -> Intent("ru.execbit.aiolauncher.APPLY_ICONS").apply {
                putExtra("packageName", pkg)
            }
            "gip" -> Intent("com.richardluo.globalIconPack.APPLY_ICON_PACK").apply {
                setPackage("com.richardluo.globalIconPack")
                putExtra("packageName", pkg)
            }
            "go" -> Intent("com.gau.go.launcherex.MyThemes.mythemeaction").apply {
                putExtra("type", 1)
                putExtra("pkgname", pkg)
            }
            "holo" -> Intent().apply {
                component = ComponentName("com.mobint.hololauncher", "com.mobint.hololauncher.SettingsActivity")
            }
            "holoics" -> Intent().apply {
                component = ComponentName("com.mobint.hololauncher.hd", "com.mobint.hololauncher.SettingsActivity")
            }
            "lucid" -> Intent("com.powerpoint45.action.APPLY_THEME").apply {
                putExtra("icontheme", pkg)
            }
            "posidon" -> Intent("posidon.launcher.APPLY_ICONS").apply {
                putExtra("iconpack", pkg)
            }
            "projectivy" -> Intent("com.spocky.projengmenu.APPLY_ICONPACK").apply {
                putExtra("packageName", pkg)
            }
            "solo" -> Intent("home.solo.launcher.free.APPLY_THEME").apply {
                putExtra("EXTRA_PACKAGENAME", pkg)
                putExtra("EXTRA_THEMENAME", appName)
            }
            "square" -> Intent("com.ss.squarehome2.ACTION_APPLY_ICONPACK").apply {
                putExtra("com.ss.squarehome2.EXTRA_ICONPACK", pkg)
            }
            "tsf" -> Intent("android.intent.action.MAIN").apply {
                component = ComponentName("com.tsf.shell", "com.tsf.shell.ShellActivity")
            }
            else -> null
        }

        try {
            if (intent != null) {
                context.startActivity(intent)
            } else {
                showManualDialog(context, launcher.name)
            }
        } catch (_: Exception) {
            try {
                if (intent != null) context.sendBroadcast(intent)
                showManualDialog(context, launcher.name)
            } catch (_: Exception) {
                showManualDialog(context, launcher.name)
            }
        }
    }

    private fun showManualDialog(context: Context, launcherName: String) {
        MaterialAlertDialogBuilder(context)
            .setTitle(launcherName)
            .setMessage(context.getString(R.string.launcher_manual_apply, launcherName))
            .setPositiveButton(android.R.string.ok, null)
            .show()
    }

    private fun resolveDefaultHomePackage(pm: PackageManager): String? {
        val homeIntent = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
        val ri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            pm.resolveActivity(homeIntent, PackageManager.ResolveInfoFlags.of(PackageManager.MATCH_DEFAULT_ONLY.toLong()))
        } else {
            @Suppress("DEPRECATION")
            pm.resolveActivity(homeIntent, PackageManager.MATCH_DEFAULT_ONLY)
        }
        return ri?.activityInfo?.packageName
    }

    private fun isPackageInstalled(pm: PackageManager, pkg: String): Boolean {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                pm.getPackageInfo(pkg, PackageManager.PackageInfoFlags.of(0L))
            } else {
                @Suppress("DEPRECATION")
                pm.getPackageInfo(pkg, 0)
            }
            true
        } catch (_: PackageManager.NameNotFoundException) {
            false
        }
    }
}
