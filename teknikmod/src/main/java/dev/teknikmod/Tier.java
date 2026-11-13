package dev.teknikmod;

/** Cihaz kademeleri ve denge degerleri (FE = Forge Energy, /t = tick basina). */
public enum Tier {
    //        onek          komur: uretim, depo, cikis   gunes: uretim, depo, cikis   batarya: depo, giris/cikis
    BASIC(    "",           40,  20_000,   200,          8,   2_000,   32,            200_000,     500),
    ADVANCED( "advanced_",  120, 60_000,   600,          32,  8_000,   128,           1_000_000,   2_000),
    ELITE(    "elite_",     360, 180_000,  1_800,        128, 32_000,  512,           5_000_000,   8_000);

    public static final int COPPER_CABLE_RATE = 250;
    public static final int GOLD_CABLE_RATE = 1_000;
    public static final int DIAMOND_CABLE_RATE = 4_000;

    /** Kayit adlarinin oneki, or. "advanced_coal_generator". */
    public final String prefix;
    public final int coalRate, coalCapacity, coalOutput;
    public final int solarRate, solarCapacity, solarOutput;
    public final int batteryCapacity, batteryIo;

    Tier(String prefix, int coalRate, int coalCapacity, int coalOutput,
         int solarRate, int solarCapacity, int solarOutput, int batteryCapacity, int batteryIo) {
        this.prefix = prefix;
        this.coalRate = coalRate;
        this.coalCapacity = coalCapacity;
        this.coalOutput = coalOutput;
        this.solarRate = solarRate;
        this.solarCapacity = solarCapacity;
        this.solarOutput = solarOutput;
        this.batteryCapacity = batteryCapacity;
        this.batteryIo = batteryIo;
    }
}
