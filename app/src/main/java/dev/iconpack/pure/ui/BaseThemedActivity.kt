package dev.iconpack.pure.ui

import android.content.res.Configuration
import android.os.Bundle
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.PreferenceManager
import com.google.android.material.color.DynamicColors
import dev.iconpack.pure.R

abstract class BaseThemedActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        val prefs = PreferenceManager.getDefaultSharedPreferences(this)
        val useAmoled = prefs.getBoolean("use_amoled", false)
        val useMaterialYou = prefs.getBoolean("use_material_you", true)
        val isNight = (resources.configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK) ==
            Configuration.UI_MODE_NIGHT_YES

        setTheme(
            when {
                useAmoled && isNight && useMaterialYou -> R.style.MyApp_Default_Amoled_MaterialYou
                useAmoled && isNight -> R.style.MyApp_Default_Amoled
                useMaterialYou -> R.style.MyApp_Default_MaterialYou
                else -> R.style.MyApp_Default
            }
        )
        if (useMaterialYou) {
            DynamicColors.applyToActivityIfAvailable(this)
        }
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
    }
}
