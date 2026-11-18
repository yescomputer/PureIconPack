package dev.iconpack.pure.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import dev.iconpack.pure.data.IconCategory
import dev.iconpack.pure.data.IconPackRepository
import dev.iconpack.pure.data.InstalledAppsStats
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {

    val repository = IconPackRepository(application)

    private val _categories = MutableStateFlow<List<IconCategory>>(emptyList())
    val categories: StateFlow<List<IconCategory>> = _categories.asStateFlow()

    private val _totalIconsCount = MutableStateFlow(4190)
    val totalIconsCount: StateFlow<Int> = _totalIconsCount.asStateFlow()

    private val _installedStats = MutableStateFlow<InstalledAppsStats?>(null)
    val installedStats: StateFlow<InstalledAppsStats?> = _installedStats.asStateFlow()

    private val _selectedCategoryIndex = MutableStateFlow(0)
    val selectedCategoryIndex: StateFlow<Int> = _selectedCategoryIndex.asStateFlow()

    private val _iconShapeIndex = MutableStateFlow(0)
    val iconShapeIndex: StateFlow<Int> = _iconShapeIndex.asStateFlow()

    private val _focusSearchTrigger = MutableStateFlow(0)
    val focusSearchTrigger: StateFlow<Int> = _focusSearchTrigger.asStateFlow()

    init {
        loadIcons()
        loadInstalledApps()
    }

    fun loadIcons() {
        viewModelScope.launch {
            val (cats, uniqueCount) = repository.loadIconCategories()
            _categories.value = cats
            if (uniqueCount > 0) {
                _totalIconsCount.value = uniqueCount
            }
        }
    }

    fun loadInstalledApps() {
        viewModelScope.launch {
            _installedStats.value = repository.scanInstalledAppsStats()
        }
    }

    fun setSelectedCategoryIndex(index: Int) {
        _selectedCategoryIndex.value = index
    }

    fun setIconShapeIndex(index: Int) {
        _iconShapeIndex.value = index
    }

    fun triggerSearchFocus() {
        _focusSearchTrigger.value += 1
    }

    fun consumeSearchFocus() {
        _focusSearchTrigger.value = 0
    }
}
