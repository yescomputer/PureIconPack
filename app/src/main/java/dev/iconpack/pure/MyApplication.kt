package dev.iconpack.pure

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate
import androidx.preference.PreferenceManager
import com.google.android.material.color.DynamicColors

class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        applySavedNightMode(this)
        val prefs = PreferenceManager.getDefaultSharedPreferences(this)
        if (prefs.getBoolean("use_material_you", true)) {
            DynamicColors.applyToActivitiesIfAvailable(this)
        }
    }

    companion object {
        fun applySavedNightMode(context: Application) {
            val prefs = PreferenceManager.getDefaultSharedPreferences(context)
            when (prefs.getString("app_theme", "system")) {
                "light" -> AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO)
                "dark" -> AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES)
                else -> AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
            }
        }
    }
}
