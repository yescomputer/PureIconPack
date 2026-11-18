package dev.iconpack.pure.ui

import android.annotation.SuppressLint
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import dev.iconpack.pure.BuildConfig
import dev.iconpack.pure.MainActivity
import dev.iconpack.pure.R
import dev.iconpack.pure.data.IconCategory
import dev.iconpack.pure.data.IconItem
import dev.iconpack.pure.util.LauncherHelper
import kotlinx.coroutines.launch

class HomeFragment : Fragment() {

    private val viewModel: MainViewModel by activityViewModels()
    private val rotationHandler = Handler(Looper.getMainLooper())
    private var previewPool: List<IconItem> = emptyList()
    private var previewOffset = 0
    private var previewRow: LinearLayout? = null

    private val rotateRunnable = object : Runnable {
        override fun run() {
            if (previewPool.size > 6 && isResumed) {
                previewOffset = (previewOffset + 6) % previewPool.size
                renderPreviewStrip()
                rotationHandler.postDelayed(this, 4500L)
            }
        }
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_home, container, false)

    @SuppressLint("DiscouragedApi")
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        view.findViewById<TextView>(R.id.tv_version_badge).text = "v${BuildConfig.VERSION_NAME}"
        previewRow = view.findViewById(R.id.preview_icons_row)

        val names = resources.getStringArray(R.array.icons_preview)
        previewPool = names.mapNotNull { name ->
            viewModel.repository.createPreviewItem(name)
        }
        renderPreviewStrip()

        val tvIconsCount = view.findViewById<TextView>(R.id.tv_icons_count)
        val tvLaunchersCount = view.findViewById<TextView>(R.id.tv_launchers_count)
        val tvThemedCount = view.findViewById<TextView>(R.id.tv_themed_count)
        val chipGroupCategories = view.findViewById<ChipGroup>(R.id.chip_group_home_categories)

        tvLaunchersCount.text = getString(R.string.counter_launchers, LauncherHelper.supportedCount)

        view.findViewById<View>(R.id.card_counter_icons).setOnClickListener {
            (activity as? MainActivity)?.navigateToTab(R.id.nav_icons)
        }
        view.findViewById<View>(R.id.card_counter_launchers).setOnClickListener {
            (activity as? MainActivity)?.navigateToTab(R.id.nav_apply)
        }
        view.findViewById<View>(R.id.card_counter_themed).setOnClickListener {
            (activity as? MainActivity)?.navigateToTab(R.id.nav_apply)
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.totalIconsCount.collect { total ->
                        tvIconsCount.text = getString(R.string.counter_icons, total)
                    }
                }
                launch {
                    viewModel.categories.collect { cats ->
                        val newCat = cats.firstOrNull()?.icons
                        if (!newCat.isNullOrEmpty() && resources.getBoolean(R.bool.home_preview_icons_from_category)) {
                            previewPool = newCat
                            previewOffset = 0
                            renderPreviewStrip()
                        }
                        populateHomeCategoryChips(chipGroupCategories, cats)
                    }
                }
                launch {
                    viewModel.installedStats.collect { stats ->
                        if (stats != null) {
                            tvThemedCount.text = getString(
                                R.string.counter_themed,
                                stats.themedCount,
                                stats.totalInstalled
                            )
                        }
                    }
                }
            }
        }
    }

    private fun populateHomeCategoryChips(chipGroup: ChipGroup, categories: List<IconCategory>) {
        if (chipGroup.childCount == categories.size) return
        chipGroup.removeAllViews()
        categories.forEachIndexed { index, cat ->
            val chip = Chip(requireContext()).apply {
                text = "${cat.title} (${cat.icons.size})"
                setOnClickListener {
                    (activity as? MainActivity)?.openIconsCategory(index)
                }
            }
            chipGroup.addView(chip)
        }
    }

    override fun onResume() {
        super.onResume()
        if (resources.getBoolean(R.bool.home_preview_icons_rotate)) {
            rotationHandler.removeCallbacks(rotateRunnable)
            rotationHandler.postDelayed(rotateRunnable, 4500L)
        }
    }

    override fun onPause() {
        rotationHandler.removeCallbacks(rotateRunnable)
        super.onPause()
    }

    override fun onDestroyView() {
        previewRow = null
        super.onDestroyView()
    }

    private fun renderPreviewStrip() {
        val row = previewRow ?: return
        row.removeAllViews()
        if (previewPool.isEmpty()) return
        val density = resources.displayMetrics.density
        val sizePx = (48 * density).toInt()
        val takeCount = minOf(6, previewPool.size)
        for (i in 0 until takeCount) {
            val icon = previewPool[(previewOffset + i) % previewPool.size]
            val iv = ImageView(requireContext()).apply {
                layoutParams = LinearLayout.LayoutParams(0, sizePx, 1f)
                scaleType = ImageView.ScaleType.FIT_CENTER
                setImageResource(icon.resId)
                setOnClickListener {
                    (activity as? MainActivity)?.onIconClicked(icon)
                }
            }
            row.addView(iv)
        }
    }
}
