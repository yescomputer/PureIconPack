package dev.iconpack.pure.ui

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.core.widget.doAfterTextChanged
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.textfield.TextInputEditText
import dev.iconpack.pure.R
import dev.iconpack.pure.data.LauncherEntry
import dev.iconpack.pure.util.LauncherHelper
import java.util.Locale

class ApplyFragment : Fragment() {

    private var allLaunchers: List<LauncherEntry> = emptyList()
    private lateinit var adapter: LaunchersAdapter

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View = inflater.inflate(R.layout.fragment_apply, container, false)

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val etSearch = view.findViewById<TextInputEditText>(R.id.et_search_launchers)
        val rv = view.findViewById<RecyclerView>(R.id.rv_launchers)
        rv.layoutManager = LinearLayoutManager(requireContext())

        allLaunchers = LauncherHelper.loadLaunchers(requireContext())
        adapter = LaunchersAdapter(allLaunchers) { entry ->
            LauncherHelper.executeLauncherApply(requireContext(), entry)
        }
        rv.adapter = adapter

        etSearch.doAfterTextChanged { text ->
            val q = text?.toString()?.trim()?.lowercase(Locale.getDefault()).orEmpty()
            val filtered = if (q.isEmpty()) {
                allLaunchers
            } else {
                allLaunchers.filter { it.name.lowercase(Locale.getDefault()).contains(q) }
            }
            adapter.submit(filtered)
        }
    }

    private class LaunchersAdapter(
        private var items: List<LauncherEntry>,
        private val onClick: (LauncherEntry) -> Unit
    ) : RecyclerView.Adapter<LaunchersAdapter.VH>() {

        fun submit(newItems: List<LauncherEntry>) {
            items = newItems
            notifyDataSetChanged()
        }

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val iv: ImageView = view.findViewById(R.id.iv_launcher_icon)
            val name: TextView = view.findViewById(R.id.tv_launcher_name)
            val status: TextView = view.findViewById(R.id.tv_launcher_status)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val v = LayoutInflater.from(parent.context).inflate(R.layout.item_launcher, parent, false)
            return VH(v)
        }

        @SuppressLint("DiscouragedApi")
        override fun onBindViewHolder(holder: VH, position: Int) {
            val ctx = holder.itemView.context
            val item = items[position]
            holder.name.text = item.name
            holder.status.text = when {
                item.isDefault -> ctx.getString(R.string.launcher_default)
                item.isInstalled -> ctx.getString(R.string.launcher_installed)
                else -> ctx.getString(R.string.launcher_not_installed)
            }
            holder.itemView.alpha = if (item.isInstalled) 1.0f else 0.72f

            val installedIcon = if (item.isInstalled) {
                item.packageNames.firstNotNullOfOrNull { pkg ->
                    try {
                        ctx.packageManager.getApplicationIcon(pkg)
                    } catch (_: Exception) {
                        null
                    }
                }
            } else null

            if (installedIcon != null) {
                holder.iv.setImageDrawable(installedIcon)
            } else {
                val mappedDrawableName = when (item.key) {
                    "adwex" -> "ic_adw_ex"
                    "googlenow" -> "ic_google_now"
                    "holoics" -> "ic_holo_ics"
                    "lg" -> "ic_lg_home"
                    "lineageos" -> "ic_lineageos_theme_engine"
                    "smartpro" -> "ic_smart_pro"
                    "square" -> "ic_square_home"
                    else -> "ic_${item.key}"
                }
                val resId = ctx.resources.getIdentifier(
                    mappedDrawableName,
                    "drawable",
                    ctx.packageName
                ).takeIf { it != 0 } ?: ctx.resources.getIdentifier(
                    item.key,
                    "drawable",
                    ctx.packageName
                ).takeIf { it != 0 } ?: R.mipmap.ic_launcher
                holder.iv.setImageResource(resId)
            }

            holder.itemView.setOnClickListener { onClick(item) }
        }

        override fun getItemCount(): Int = items.size
    }
}
