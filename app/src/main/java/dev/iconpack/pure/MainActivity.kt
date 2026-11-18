package dev.iconpack.pure

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import androidx.activity.viewModels
import androidx.core.content.ContextCompat
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updateLayoutParams
import androidx.fragment.app.Fragment
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.floatingactionbutton.ExtendedFloatingActionButton
import dev.iconpack.pure.data.IconItem
import dev.iconpack.pure.ui.ApplyFragment
import dev.iconpack.pure.ui.BaseThemedActivity
import dev.iconpack.pure.ui.HelpActivity
import dev.iconpack.pure.ui.HomeFragment
import dev.iconpack.pure.ui.IconInfoBottomSheet
import dev.iconpack.pure.ui.IconsFragment
import dev.iconpack.pure.ui.MainViewModel
import dev.iconpack.pure.ui.SettingsActivity
import dev.iconpack.pure.util.IconPickerHelper
import dev.iconpack.pure.util.LauncherHelper

class MainActivity : BaseThemedActivity() {

    private val viewModel: MainViewModel by viewModels()
    var pickerMode: Int = IconPickerHelper.PICKER_NONE
        private set

    private lateinit var bottomNav: BottomNavigationView
    private lateinit var mainFab: ExtendedFloatingActionButton

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        pickerMode = IconPickerHelper.resolvePickerMode(intent)

        val root = findViewById<View>(R.id.root_coordinator)
        val appBar = findViewById<View>(R.id.app_bar)
        val fragmentContainer = findViewById<View>(R.id.fragment_container)
        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        val pickerBanner = findViewById<View>(R.id.picker_banner)
        bottomNav = findViewById(R.id.bottom_nav)
        mainFab = findViewById(R.id.main_fab)

        val density = resources.displayMetrics.density
        val navBaseHeight = (80 * density).toInt()
        val fabBaseMargin = (96 * density).toInt()
        ViewCompat.setOnApplyWindowInsetsListener(root) { _, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            appBar.setPadding(bars.left, bars.top, bars.right, 0)
            bottomNav.setPadding(bars.left, 0, bars.right, bars.bottom)
            fragmentContainer.updateLayoutParams<ViewGroup.MarginLayoutParams> {
                bottomMargin = navBaseHeight + bars.bottom
            }
            mainFab.updateLayoutParams<ViewGroup.MarginLayoutParams> {
                bottomMargin = fabBaseMargin + bars.bottom
            }
            insets
        }

        if (IconPickerHelper.isExternalIconPicker(pickerMode)) {
            pickerBanner.visibility = View.VISIBLE
        }

        toolbar.setOnMenuItemClickListener { item ->
            when (item.itemId) {
                R.id.action_help -> {
                    startActivity(Intent(this, HelpActivity::class.java))
                    true
                }
                R.id.action_settings -> {
                    startActivity(Intent(this, SettingsActivity::class.java))
                    true
                }
                else -> false
            }
        }

        bottomNav.setOnItemSelectedListener { item ->
            switchTab(item.itemId)
            true
        }

        if (savedInstanceState == null) {
            if (!handleShortcutIntent(intent)) {
                val initialTab = when (pickerMode) {
                    IconPickerHelper.ICONS_PICKER, IconPickerHelper.IMAGE_PICKER -> R.id.nav_icons
                    else -> R.id.nav_home
                }
                bottomNav.selectedItemId = initialTab
            }
        } else {
            updateFabForTab(bottomNav.selectedItemId)
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleShortcutIntent(intent)
    }

    private fun handleShortcutIntent(intent: Intent?): Boolean {
        return when (intent?.action) {
            ACTION_SHORTCUT_SEARCH -> {
                bottomNav.selectedItemId = R.id.nav_icons
                viewModel.triggerSearchFocus()
                true
            }
            ACTION_SHORTCUT_APPLY -> {
                bottomNav.selectedItemId = R.id.nav_apply
                true
            }
            else -> false
        }
    }

    fun navigateToTab(itemId: Int) {
        bottomNav.selectedItemId = itemId
    }

    fun openIconsCategory(categoryIndex: Int) {
        viewModel.setSelectedCategoryIndex(categoryIndex)
        bottomNav.selectedItemId = R.id.nav_icons
    }

    fun onIconClicked(icon: IconItem) {
        IconInfoBottomSheet.newInstance(icon)
            .show(supportFragmentManager, "icon_info_sheet")
    }

    private fun switchTab(itemId: Int) {
        val tag = "tab_$itemId"
        val fm = supportFragmentManager
        val current = fm.fragments.firstOrNull { it.isVisible }
        var target: Fragment? = fm.findFragmentByTag(tag)

        val tx = fm.beginTransaction()
        if (current != null && current !== target) {
            tx.hide(current)
        }
        if (target == null) {
            target = when (itemId) {
                R.id.nav_icons -> IconsFragment()
                R.id.nav_apply -> ApplyFragment()
                else -> HomeFragment()
            }
            tx.add(R.id.fragment_container, target, tag)
        } else {
            tx.show(target)
        }
        tx.commitNowAllowingStateLoss()
        updateFabForTab(itemId)
    }

    private fun updateFabForTab(itemId: Int) {
        if (itemId == R.id.nav_home) {
            mainFab.show()
            mainFab.icon = ContextCompat.getDrawable(this, R.drawable.ic_apply)
            mainFab.text = getString(R.string.quick_apply)
            mainFab.setOnClickListener {
                LauncherHelper.applyForDefaultOrSelected(this)
            }
        } else {
            mainFab.hide()
        }
    }

    companion object {
        const val ACTION_SHORTCUT_SEARCH = "dev.iconpack.pure.SHORTCUT_SEARCH"
        const val ACTION_SHORTCUT_APPLY = "dev.iconpack.pure.SHORTCUT_APPLY"
    }
}
