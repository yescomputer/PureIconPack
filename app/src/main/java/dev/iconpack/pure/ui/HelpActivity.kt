package dev.iconpack.pure.ui

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import dev.iconpack.pure.R

class HelpActivity : BaseThemedActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_simple_list)

        val toolbar = findViewById<MaterialToolbar>(R.id.toolbar)
        toolbar.setTitle(R.string.help)
        toolbar.setNavigationOnClickListener { finish() }

        val questions = resources.getStringArray(R.array.questions)
        val answers = resources.getStringArray(R.array.answers)
        val pairs = (0 until minOf(questions.size, answers.size)).map { i ->
            questions[i] to answers[i]
        }

        val rv = findViewById<RecyclerView>(R.id.rv_list)
        val root = findViewById<View>(R.id.root_simple_list)
        val density = resources.displayMetrics.density
        val basePad = (16 * density).toInt()
        androidx.core.view.ViewCompat.setOnApplyWindowInsetsListener(root) { v, insets ->
            val bars = insets.getInsets(androidx.core.view.WindowInsetsCompat.Type.systemBars())
            v.setPadding(bars.left, bars.top, bars.right, 0)
            rv.setPadding(basePad, basePad, basePad, basePad + bars.bottom)
            insets
        }
        rv.layoutManager = LinearLayoutManager(this)
        rv.adapter = FaqAdapter(pairs)
    }

    private class FaqAdapter(
        private val items: List<Pair<String, String>>
    ) : RecyclerView.Adapter<FaqAdapter.VH>() {

        class VH(view: View) : RecyclerView.ViewHolder(view) {
            val q: TextView = view.findViewById(R.id.tv_question)
            val a: TextView = view.findViewById(R.id.tv_answer)
        }

        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
            val v = LayoutInflater.from(parent.context).inflate(R.layout.item_faq, parent, false)
            return VH(v)
        }

        override fun onBindViewHolder(holder: VH, position: Int) {
            val (qText, aText) = items[position]
            holder.q.text = qText
            holder.a.text = aText
        }

        override fun getItemCount(): Int = items.size
    }
}
