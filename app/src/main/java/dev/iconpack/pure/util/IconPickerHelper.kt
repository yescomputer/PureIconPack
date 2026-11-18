package dev.iconpack.pure.util

import android.app.Activity
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.core.content.FileProvider
import dev.iconpack.pure.data.IconItem
import java.io.File
import java.io.FileOutputStream

object IconPickerHelper {
    const val PICKER_NONE = 0
    const val ICONS_PICKER = 1
    const val IMAGE_PICKER = 2

    private val ICON_PICKER_ACTIONS = setOf(
        "org.adw.launcher.icons.ACTION_PICK_ICON",
        "com.novalauncher.THEME",
        "ch.deletescape.lawnchair.ICONPACK",
        "net.oneplus.launcher.icons.ACTION_PICK_ICON",
        "com.spocky.projengmenu.icons.ACTION_PICK_ICON",
        "com.phonemetra.turbo.launcher.icons.ACTION_PICK_ICON",
        "jp.co.a_tm.android.launcher.icons.ACTION_PICK_ICON"
    )

    fun resolvePickerMode(intent: Intent?): Int {
        val action = intent?.action ?: return PICKER_NONE
        return when {
            action in ICON_PICKER_ACTIONS -> ICONS_PICKER
            action == Intent.ACTION_PICK || action == Intent.ACTION_GET_CONTENT -> IMAGE_PICKER
            else -> PICKER_NONE
        }
    }

    fun isExternalIconPicker(mode: Int): Boolean = mode == ICONS_PICKER || mode == IMAGE_PICKER

    @Suppress("DEPRECATION")
    fun finishWithSelectedIcon(activity: Activity, icon: IconItem, pickerMode: Int) {
        val resultIntent = Intent()
        val rawBitmap = BitmapFactory.decodeResource(activity.resources, icon.resId)
        if (rawBitmap == null) {
            activity.setResult(Activity.RESULT_CANCELED, resultIntent)
            activity.finish()
            return
        }

        when (pickerMode) {
            ICONS_PICKER -> {
                val safeCopy = rawBitmap.config?.let { rawBitmap.copy(it, false) } ?: rawBitmap
                resultIntent.putExtra("icon", safeCopy)
                val iconRes = Intent.ShortcutIconResource.fromContext(activity, icon.resId)
                resultIntent.putExtra(Intent.EXTRA_SHORTCUT_ICON_RESOURCE, iconRes)
            }
            IMAGE_PICKER -> {
                val pickerDir = File(activity.cacheDir, "picked_icons").apply { mkdirs() }
                val outFile = File(pickerDir, "${icon.drawableName}.png")
                FileOutputStream(outFile).use { fos ->
                    rawBitmap.compress(Bitmap.CompressFormat.PNG, 100, fos)
                }
                val uri = FileProvider.getUriForFile(
                    activity,
                    "${activity.packageName}.fileProvider",
                    outFile
                )
                resultIntent.putExtra(Intent.EXTRA_STREAM, uri)
                resultIntent.data = uri
                resultIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                resultIntent.putExtra("return-data", false)
            }
        }
        resultIntent.putExtra("picker_key", pickerMode)
        activity.setResult(Activity.RESULT_OK, resultIntent)
        activity.finish()
    }
}
