package dev.iconpack.pure.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.view.children
import androidx.core.widget.doAfterTextChanged
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.button.MaterialButton
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.imageview.ShapeableImageView
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.shape.CornerFamily
import com.google.android.material.shape.RelativeCornerSize
import com.google.android.material.shape.ShapeAppearanceModel
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import dev.iconpack.pure.MainActivity
import dev.iconpack.pure.R
import dev.iconpack.pure.data.IconCategory
import dev.iconpack.pure.data.IconItem
import kotlinx.coroutines.launch
import java.util.Locale

class IconsFragment : Fragment() {

    private val viewModel: MainViewModel by activityViewModels()
    private var searchQuery = ""
    private lateinit var iconsAdapter: IconsGridAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_icons, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val tilSearch = view.findViewById<TextInputLayout>(R.id.til_search_icons)
        val etSearch = view.findViewById<TextInputEditText>(R.id.et_search_icons)
        val btnShape = view.findViewById<MaterialButton>(R.id.btn_icon_shape)
        val chipGroup = view.findViewById<ChipGroup>(R.id.chip_group_categories)
        val rvIcons = view.findViewById<RecyclerView>(R.id.rv_icons)
        val progress = view.findViewById<CircularProgressIndicator>(R.id.progress_icons)

        val spanCount = resources.getInteger(R.integer.icons_columns_count)
        rvIcons.layoutManager = GridLayoutManager(requireContext(), spanCount)
        rvIcons.setHasFixedSize(true)

        iconsAdapter = IconsGridAdapter { icon ->
            (activity as? MainActivity)?.onIconClicked(icon)
        }
        rvIcons.adapter = iconsAdapter

        etSearch.doAfterTextChanged { text ->
            searchQuery = text?.toString()?.trim().orEmpty()
            applyFilter(viewModel.categories.value, viewModel.selectedCategoryIndex.value)
        }

        btnShape.setOnClickListener {
            val shapes = resources.getStringArray(R.array.icon_shapes_entries)
            MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.icon_shape)
                .setSingleChoiceItems(shapes, viewModel.iconShapeIndex.value) { dialog, which ->
                    viewModel.setIconShapeIndex(which)
                    dialog.dismiss()
                }
                .show()
        }

        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.totalIconsCount.collect { count ->
                        tilSearch.hint = getString(R.string.search_icons, count)
                    }
                }
                launch {
                    viewModel.iconShapeIndex.collect { shapeIdx ->
                        iconsAdapter.updateShapeIndex(shapeIdx)
                    }
                }
                launch {
                    viewModel.categories.collect { cats ->
                        progress.visibility = if (cats.isEmpty()) View.VISIBLE else View.GONE
                        populateCategoryChips(chipGroup, cats, viewModel.selectedCategoryIndex.value)
                        applyFilter(cats, viewModel.selectedCategoryIndex.value)
                    }
                }
                launch {
                    viewModel.selectedCategoryIndex.collect { selectedIdx ->
                        syncSelectedChip(chipGroup, selectedIdx)
                        applyFilter(viewModel.categories.value, selectedIdx)
                    }
                }
                launch {
                    viewModel.focusSearchTrigger.collect { count ->
                        if (count > 0) {
                            viewModel.consumeSearchFocus()
                            etSearch.post {
                                etSearch.requestFocus()
                                val imm = requireContext().getSystemService(android.view.inputmethod.InputMethodManager::class.java)
                                imm?.showSoftInput(etSearch, android.view.inputmethod.InputMethodManager.SHOW_IMPLICIT)
                            }
                        }
                    }
                }
            }
        }
    }

    private fun populateCategoryChips(
        chipGroup: ChipGroup,
        categories: List<IconCategory>,
        selectedIndex: Int
    ) {
        if (chipGroup.childCount == categories.size) {
            syncSelectedChip(chipGroup, selectedIndex)
            return
        }
        chipGroup.removeAllViews()
        categories.forEachIndexed { index, cat ->
            val chip = Chip(requireContext()).apply {
                id = View.generateViewId()
                isCheckable = true
                text = "${cat.title} (${cat.icons.size})"
                isChecked = index == selectedIndex
                setOnClickListener {
                    viewModel.setSelectedCategoryIndex(index)
                }
            }
            chipGroup.addView(chip)
        }
    }

    private fun syncSelectedChip(chipGroup: ChipGroup, selectedIndex: Int) {
        chipGroup.children.forEachIndexed { idx, child ->
            if (child is Chip && child.isChecked != (idx == selectedIndex)) {
                child.isChecked = idx == selectedIndex
            }
        }
    }

    private fun applyFilter(categories: List<IconCategory>, selectedCategoryIndex: Int) {
        if (categories.isEmpty()) return
        val tokens = searchQuery.lowercase(Locale.ROOT).split(' ').filter { it.isNotBlank() }
        val list = if (tokens.isEmpty()) {
            categories.getOrElse(selectedCategoryIndex) { categories.last() }.icons
        } else {
            val allIcons = categories.last().icons
            allIcons.filter { icon ->
                tokens.all { token -> icon.searchBlob.contains(token) }
            }
        }
        iconsAdapter.submitList(list)
    }

    private class IconsGridAdapter(
        private val onClick: (IconItem) -> Unit
    ) : ListAdapter<IconItem, IconsGridAdapter.VH>(DIFF) {

        private var shapeModel: ShapeAppearanceModel = buildShapeModel(0)

        fun updateShapeIndex(index: Int) {
            shapeModel = buildShapeModel(index)
            notifyDataSetChanged()
        }

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val iv: ShapeableImageView = view.findViewById(R.id.iv_icon)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val v = LayoutInflater.from(parent.context).inflate(R.layout.item_icon, parent, false)
            return VH(v)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val item = getItem(position)
            holder.iv.shapeAppearanceModel = shapeModel
            holder.iv.setImageResource(item.resId)
            holder.itemView.contentDescription = item.displayName
            holder.itemView.setOnClickListener { onClick(item) }
        }

        companion object {
            private val DIFF = object : DiffUtil.ItemCallback<IconItem>() {
                override fun areItemsTheSame(oldItem: IconItem, newItem: IconItem): Boolean =
                    oldItem.drawableName == newItem.drawableName

                override fun areContentsTheSame(oldItem: IconItem, newItem: IconItem): Boolean =
                    oldItem == newItem
            }
        }
    }

    companion object {
        fun buildShapeModel(index: Int): ShapeAppearanceModel {
            val b = ShapeAppearanceModel.builder()
            return when (index) {
                1 -> b.setAllCornerSizes(RelativeCornerSize(0.5f)).build()
                2 -> b.setAllCornerSizes(RelativeCornerSize(0.32f)).build()
                3 -> b.setAllCornerSizes(RelativeCornerSize(0.22f)).build()
                4 -> b.setAllCornerSizes(RelativeCornerSize(0.06f)).build()
                5 -> b
                    .setTopLeftCorner(CornerFamily.ROUNDED, RelativeCornerSize(0.5f))
                    .setTopRightCorner(CornerFamily.ROUNDED, RelativeCornerSize(0.5f))
                    .setBottomLeftCorner(CornerFamily.ROUNDED, RelativeCornerSize(0.5f))
                    .setBottomRightCorner(CornerFamily.ROUNDED, RelativeCornerSize(0.12f))
                    .build()
                else -> b.setAllCornerSizes(0f).build()
            }
        }
    }
}
