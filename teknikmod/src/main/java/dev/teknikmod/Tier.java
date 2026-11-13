package dev.teknikmod;

/** Cihaz kademeleri ve denge degerleri (FE = Forge Energy, /t = tick basina). */
public enum Tier {
    BASIC("", 1), ADVANCED("advanced_", 2), ELITE("elite_", 3),
    /** Yakit, gunes ve enerji gerektirmez; depolari hic bosalmaz. Tarifi yoktur (ileride ozel masada uretilecek). */
    CREATIVE("creative_", 4);

    public static final int COPPER_CABLE_RATE = 250;
    public static final int GOLD_CABLE_RATE = 1_000;
    public static final int DIAMOND_CABLE_RATE = 4_000;
    public static final int CREATIVE_CABLE_RATE = Integer.MAX_VALUE;
    /** Yaratici cihazlarin tick basina verebildigi enerji. */
    public static final int CREATIVE_POWER = 10_000_000;

    /** Kayit adlarinin oneki, or. "advanced_coal_generator". */
    public final String prefix;
    public final boolean creative;

    // Komur jeneratoru: uretim, depo, cikis
    public final int coalRate, coalCapacity, coalOutput;
    // Gunes paneli: uretim, depo, cikis
    public final int solarRate, solarCapacity, solarOutput;
    // Batarya: depo, giris/cikis
    public final int batteryCapacity, batteryIo;
    /**
     * Islem makineleri (elektrikli firin, ogutucu): hiz carpani, tuketim, depo, giris.
     * Islem suresi = tarif suresi / machineSpeed. Hiz ve tuketim birlikte arttigi icin
     * esya basina enerji her kademede aynidir (firinda 4.000 FE).
     */
    public final int machineSpeed, machineUse, machineCapacity, machineInput;

    Tier(String prefix, int level) {
        this.prefix = prefix;
        this.creative = level == 4;
        if (creative) {
            coalRate = coalCapacity = coalOutput = CREATIVE_POWER;
            solarRate = solarCapacity = solarOutput = CREATIVE_POWER;
            batteryCapacity = 2_000_000_000;
            batteryIo = CREATIVE_POWER;
            machineSpeed = 200;        // her islem 1 tick
            machineUse = 0;
            machineCapacity = 80_000;
            machineInput = 0;
            return;
        }
        int x3 = level == 1 ? 1 : level == 2 ? 3 : 9;    // 1, 3, 9
        int x4 = level == 1 ? 1 : level == 2 ? 4 : 16;   // 1, 4, 16
        int x2 = 1 << (level - 1);                       // 1, 2, 4

        coalRate = 40 * x3;            // 40, 120, 360
        coalCapacity = 20_000 * x3;
        coalOutput = 200 * x3;

        solarRate = 8 * x4;            // 8, 32, 128
        solarCapacity = 2_000 * x4;
        solarOutput = 32 * x4;

        batteryCapacity = level == 1 ? 200_000 : level == 2 ? 1_000_000 : 5_000_000;
        batteryIo = 500 * x4;          // 500, 2.000, 8.000

        machineSpeed = 2 * x2;         // 2x, 4x, 8x (normal firina gore)
        machineUse = 40 * x2;          // 40, 80, 160
        machineCapacity = 20_000 * x2;
        machineInput = 200 * x2;
    }
}
