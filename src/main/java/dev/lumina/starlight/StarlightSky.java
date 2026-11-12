package dev.lumina.starlight;

import net.minecraft.core.BlockPos;
import net.minecraft.util.Mth;
import net.minecraft.world.level.Level;

/**
 * Works out how much starlight reaches a position. The result is a factor in [0, 1] built from:
 * time of night, moon phase, altitude, weather and whether the sky is actually visible.
 */
public final class StarlightSky {
    /** Starlight starts shortly after sunset ... */
    public static final int NIGHT_START = 12500;
    /** ... and fades out shortly before sunrise. */
    public static final int NIGHT_END = 23500;

    private StarlightSky() {
    }

    /** 0 during the day, rising smoothly to 1 at midnight (tick 18000). */
    public static float nightFactor(long dayTime) {
        long time = Math.floorMod(dayTime, 24000L);
        if (time <= NIGHT_START || time >= NIGHT_END) {
            return 0.0F;
        }
        float progress = (time - NIGHT_START) / (float) (NIGHT_END - NIGHT_START);
        return Mth.sin(progress * Mth.PI);
    }

    /** New moon still gives 60%, full moon gives 100%. */
    public static float moonFactor(Level level) {
        return 0.6F + 0.4F * level.getMoonBrightness();
    }

    /** Higher is better: 50% at sea-floor depths, 100% from y=200 upwards. */
    public static float altitudeFactor(int y) {
        return 0.5F + 0.5F * Mth.clamp((y - 40) / 160.0F, 0.0F, 1.0F);
    }

    /** Clouds dim the stars. */
    public static float weatherFactor(Level level) {
        if (level.isThundering()) {
            return 0.25F;
        }
        return level.isRaining() ? 0.5F : 1.0F;
    }

    public static boolean hasStars(Level level) {
        return level.dimensionType().hasSkyLight() && !level.dimensionType().hasCeiling();
    }

    /** Combined starlight intensity for a collector standing at {@code pos}. */
    public static float intensity(Level level, BlockPos pos) {
        if (!hasStars(level)) {
            return 0.0F;
        }
        float night = nightFactor(level.getDayTime());
        if (night <= 0.0F || !level.canSeeSky(pos.above())) {
            return 0.0F;
        }
        return night * moonFactor(level) * altitudeFactor(pos.getY()) * weatherFactor(level);
    }
}
