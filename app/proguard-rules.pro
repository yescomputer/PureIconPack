# Preserve dynamically resolved icon pack drawables and XML mappings (including R.drawable reflection)
-keep class dev.iconpack.pure.R$drawable {
    public static <fields>;
}
-keep class dev.iconpack.pure.R$xml {
    public static <fields>;
}
