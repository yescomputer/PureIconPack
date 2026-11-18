package dev.iconpack.pure.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.core.content.FileProvider
import androidx.fragment.app.activityViewModels
import androidx.lifecycle.lifecycleScope
import com.google.android.material.bottomsheet.BottomSheetDialogFragment
import com.google.android.material.button.MaterialButton
import com.google.android.material.chip.Chip
import com.google.android.material.imageview.ShapeableImageView
import dev.iconpack.pure.MainActivity
import dev.iconpack.pure.R
import dev.iconpack.pure.data.IconItem
import dev.iconpack.pure.util.IconPickerHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream

class IconInfoBottomSheet : BottomSheetDialogFragment() {

    private val viewModel: MainViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.sheet_icon_info, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val args = requireArguments()
        val drawableName = args.getString(ARG_DRAWABLE_NAME).orEmpty()
        val displayName = args.getString(ARG_DISPLAY_NAME).orEmpty()
        val resId = args.getInt(ARG_RES_ID)

        val ivIcon = view.findViewById<ShapeableImageView>(R.id.iv_sheet_icon)
        val tvTitle = view.findViewById<TextView>(R.id.tv_sheet_title)
        val chipDrawable = view.findViewById<Chip>(R.id.chip_drawable_name)
        val btnPick = view.findViewById<MaterialButton>(R.id.btn_sheet_pick)
        val btnSave = view.findViewById<MaterialButton>(R.id.btn_sheet_save)
        val btnShare = view.findViewById<MaterialButton>(R.id.btn_sheet_share)
        val containerMapped = view.findViewById<LinearLayout>(R.id.container_mapped_components)

        ivIcon.shapeAppearanceModel = IconsFragment.buildShapeModel(viewModel.iconShapeIndex.value)
        ivIcon.setImageResource(resId)
        tvTitle.text = displayName

        val drawableRef = "@drawable/$drawableName"
        chipDrawable.text = drawableRef
        chipDrawable.setOnClickListener {
            copyToClipboard(drawableRef)
        }

        val host = activity as? MainActivity
        if (host != null && IconPickerHelper.isExternalIconPicker(host.pickerMode)) {
            btnPick.visibility = View.VISIBLE
            btnPick.setOnClickListener {
                IconPickerHelper.finishWithSelectedIcon(
                    host,
                    IconItem(drawableName, displayName, resId),
                    host.pickerMode
                )
                dismiss()
            }
        }

        btnSave.setOnClickListener {
            saveIconPngToGallery(drawableName, resId)
        }

        btnShare.setOnClickListener {
            shareIconPng(drawableName, displayName, resId)
        }

        viewLifecycleOwner.lifecycleScope.launch {
            val mapped = viewModel.repository.getMappedComponents(drawableName)
            containerMapped.removeAllViews()
            if (mapped.isEmpty()) {
                val tvEmpty = TextView(requireContext()).apply {
                    text = getString(R.string.no_mapped_components)
                    alpha = 0.7f
                }
                containerMapped.addView(tvEmpty)
            } else {
                val inflater = LayoutInflater.from(requireContext())
                for (entry in mapped) {
                    val row = inflater.inflate(R.layout.item_mapped_component, containerMapped, false)
                    row.findViewById<TextView>(R.id.tv_comp_app_label).text = entry.appLabel
                    row.findViewById<TextView>(R.id.tv_comp_value).text = entry.componentInfo
                    row.findViewById<TextView>(R.id.tv_comp_installed_badge).visibility =
                        if (entry.isInstalled) View.VISIBLE else View.GONE
                    row.setOnClickListener {
                        copyToClipboard(entry.componentInfo)
                    }
                    containerMapped.addView(row)
                }
            }
        }
    }

    private fun copyToClipboard(text: String) {
        val cm = requireContext().getSystemService(ClipboardManager::class.java) ?: return
        cm.setPrimaryClip(ClipData.newPlainText("icon_info", text))
        Toast.makeText(
            requireContext(),
            getString(R.string.copied_to_clipboard, text),
            Toast.LENGTH_SHORT
        ).show()
    }

    private fun saveIconPngToGallery(drawableName: String, resId: Int) {
        val appCtx = requireContext().applicationContext
        viewLifecycleOwner.lifecycleScope.launch {
            val fileName = "$drawableName.png"
            val ok = withContext(Dispatchers.IO) {
                val bmp = BitmapFactory.decodeResource(appCtx.resources, resId) ?: return@withContext false
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                        val values = ContentValues().apply {
                            put(MediaStore.Images.Media.DISPLAY_NAME, fileName)
                            put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                            put(MediaStore.Images.Media.RELATIVE_PATH, "${Environment.DIRECTORY_PICTURES}/PureIconPack")
                        }
                        val uri = appCtx.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
                            ?: return@withContext false
                        appCtx.contentResolver.openOutputStream(uri)?.use { out ->
                            bmp.compress(Bitmap.CompressFormat.PNG, 100, out)
                        } ?: false
                    } else {
                        val dir = File(appCtx.cacheDir, "saved_icons").apply { mkdirs() }
                        FileOutputStream(File(dir, fileName)).use { out ->
                            bmp.compress(Bitmap.CompressFormat.PNG, 100, out)
                        }
                    }
                } catch (_: Exception) {
                    false
                }
            }
            if (ok) {
                Toast.makeText(
                    requireContext(),
                    getString(R.string.icon_saved_to_pictures, fileName),
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    private fun shareIconPng(drawableName: String, displayName: String, resId: Int) {
        val ctx = requireContext()
        viewLifecycleOwner.lifecycleScope.launch {
            val uri = withContext(Dispatchers.IO) {
                val bmp = BitmapFactory.decodeResource(ctx.resources, resId) ?: return@withContext null
                val shareDir = File(ctx.cacheDir, "shared_icons").apply { mkdirs() }
                val file = File(shareDir, "$drawableName.png")
                FileOutputStream(file).use { out ->
                    bmp.compress(Bitmap.CompressFormat.PNG, 100, out)
                }
                FileProvider.getUriForFile(ctx, "${ctx.packageName}.fileProvider", file)
            } ?: return@launch

            val sendIntent = Intent(Intent.ACTION_SEND).apply {
                type = "image/png"
                putExtra(Intent.EXTRA_STREAM, uri)
                putExtra(Intent.EXTRA_TEXT, "$displayName (@drawable/$drawableName)")
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(sendIntent, displayName))
        }
    }

    companion object {
        private const val ARG_DRAWABLE_NAME = "drawable_name"
        private const val ARG_DISPLAY_NAME = "display_name"
        private const val ARG_RES_ID = "res_id"

        fun newInstance(icon: IconItem): IconInfoBottomSheet {
            return IconInfoBottomSheet().apply {
                arguments = Bundle().apply {
                    putString(ARG_DRAWABLE_NAME, icon.drawableName)
                    putString(ARG_DISPLAY_NAME, icon.displayName)
                    putInt(ARG_RES_ID, icon.resId)
                }
            }
        }
    }
}
