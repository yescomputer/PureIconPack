package dev.iconpack.pure.ui

import android.os.Bundle
import androidx.preference.ListPreference
import androidx.preference.Preference
import androidx.preference.PreferenceFragmentCompat
import androidx.preference.SwitchPreferenceCompat
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.snackbar.Snackbar
import dev.iconpack.pure.BuildConfig
import dev.iconpack.pure.MyApplication
import dev.iconpack.pure.R
import java.io.File
import java.util.Locale

class SettingsActivity : BaseThemedActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        toolbar.setNavigationOnClickListener { finish() }

        val root = findViewById<android.view.View>(R.id.root_settings)
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(root) { v, insets ->
            val bars = insets.getInsets(androidx.core.view.WindowInsetsCompat.Type.systemBars())
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        if (savedInstanceState == null) {
            supportFragmentManager
                .beginTransaction()
                .replace(R.id.settings_container, SettingsFragment())
                .commit()
        }
    }

    class SettingsFragment : PreferenceFragmentCompat() {
        override fun onCreatePreferences(savedInstanceState: Bundle?, rootKey: String?) {
            setPreferencesFromResource(R.xml.preferences, rootKey)

            findPreference<Preference>("app_version")?.summary =
                "${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})"

            findPreference<ListPreference>("app_theme")?.setOnPreferenceChangeListener { _, newValue ->
                val app = requireActivity().application as MyApplication
                preferenceManager.sharedPreferences?.edit()
                    ?.putString("app_theme", newValue as? String ?: "system")
                    ?.apply()
                MyApplication.applySavedNightMode(app)
                requireActivity().recreate()
                true
            }

            findPreference<SwitchPreferenceCompat>("use_amoled")?.setOnPreferenceChangeListener { _, _ ->
                requireActivity().window.decorView.post { requireActivity().recreate() }
                true
            }

            findPreference<SwitchPreferenceCompat>("use_material_you")?.setOnPreferenceChangeListener { _, _ ->
                requireActivity().window.decorView.post { requireActivity().recreate() }
                true
            }

            findPreference<Preference>("clear_data_cache")?.setOnPreferenceClickListener {
                val freed = deleteDirContents(requireContext().cacheDir)
                val mb = String.format(Locale.US, "%.2f MB", freed / (1024.0 * 1024.0))
                view?.let { v ->
                    Snackbar.make(v, getString(R.string.pref_cache_cleared, mb), Snackbar.LENGTH_SHORT).show()
                }
                true
            }
        }

        private fun deleteDirContents(dir: File?): Long {
            if (dir == null || !dir.exists()) return 0L
            var bytes = 0L
            dir.listFiles()?.forEach { child ->
                bytes += if (child.isDirectory) {
                    val sub = deleteDirContents(child)
                    child.delete()
                    sub
                } else {
                    val len = child.length()
                    if (child.delete()) len else 0L
                }
            }
            return bytes
        }
    }
}
