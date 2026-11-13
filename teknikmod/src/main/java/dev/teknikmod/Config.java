package dev.teknikmod;

/** Denge degerleri (FE = Forge Energy). */
public final class Config {
    public static final int COAL_GENERATOR_RATE = 40;       // FE/tick uretim
    public static final int COAL_GENERATOR_CAPACITY = 20_000;
    public static final int COAL_GENERATOR_OUTPUT = 200;    // FE/tick cikis

    public static final int SOLAR_PANEL_RATE = 8;           // FE/tick (acik havada, gunduz)
    public static final int SOLAR_PANEL_CAPACITY = 2_000;
    public static final int SOLAR_PANEL_OUTPUT = 32;

    public static final int BATTERY_CAPACITY = 200_000;
    public static final int BATTERY_IO = 500;               // FE/tick giris/cikis

    public static final int COPPER_CABLE_RATE = 250;        // FE/tick
    public static final int GOLD_CABLE_RATE = 1_000;        // FE/tick

    private Config() {}
}
