import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

val keystorePath = System.getenv("KEYSTORE_PATH") ?: providers.gradleProperty("KEYSTORE_PATH").orNull
val keystorePassword = System.getenv("KEYSTORE_PASSWORD") ?: providers.gradleProperty("KEYSTORE_PASSWORD").orNull
val releaseKeyAlias = System.getenv("KEY_ALIAS") ?: providers.gradleProperty("KEY_ALIAS").orNull
val releaseKeyPassword = System.getenv("KEY_PASSWORD") ?: providers.gradleProperty("KEY_PASSWORD").orNull
val hasReleaseSigning = !keystorePath.isNullOrBlank() &&
    !keystorePassword.isNullOrBlank() &&
    !releaseKeyAlias.isNullOrBlank() &&
    !releaseKeyPassword.isNullOrBlank() &&
    file(keystorePath).exists()

val overrideVersionCode = providers.gradleProperty("versionCode").orNull?.toIntOrNull()
val overrideVersionName = providers.gradleProperty("versionName").orNull?.takeIf { it.isNotBlank() }

android {
    namespace = "dev.iconpack.pure"
    compileSdk = 36

    defaultConfig {
        applicationId = "dev.iconpack.pure"
        minSdk = 23
        targetSdk = 36
        versionCode = overrideVersionCode ?: 2026070801
        versionName = overrideVersionName ?: "20260708"
    }

    signingConfigs {
        if (hasReleaseSigning) {
            create("release") {
                storeFile = file(keystorePath!!)
                storePassword = keystorePassword
                keyAlias = releaseKeyAlias
                keyPassword = releaseKeyPassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = false
            if (hasReleaseSigning) {
                signingConfig = signingConfigs.getByName("release")
            }
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(JvmTarget.JVM_17)
        }
    }

    buildFeatures {
        buildConfig = true
    }

    androidResources {
        generateLocaleConfig = true
        noCompress += listOf("ttf")
    }

    dependenciesInfo {
        includeInApk = false
        includeInBundle = false
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.activity.ktx)
    implementation(libs.androidx.fragment.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.recyclerview)
    implementation(libs.androidx.preference.ktx)
    implementation(libs.google.material)
    implementation(libs.kotlinx.coroutines.android)
}
