package com.tahaakhan.spellmod.mana;

import com.tahaakhan.spellmod.registry.ModAttachments;
import net.minecraft.world.entity.player.Player;

/** The rules of the mana system. All tuning numbers live here. */
public final class Mana {
    /** Chance for raw mana to drop from a broken block with no experience at all (0.2%). */
    public static final float BASE_FIND_CHANCE = 0.002F;
    /** Extra chance per point of mana experience. */
    public static final float FIND_CHANCE_PER_EXPERIENCE = 0.0004F;
    /** The chance never gets better than this (5%). */
    public static final float MAX_FIND_CHANCE = 0.05F;

    /** Mana experience gained each time raw mana is found. */
    public static final int EXPERIENCE_PER_FIND = 1;
    /** Mana experience gained each time refined mana is absorbed. */
    public static final int EXPERIENCE_PER_ABSORB = 2;

    /** Mana contained in one piece of refined mana. */
    public static final int MANA_PER_REFINED = 10;
    /** How much the body's capacity grows with each absorption. */
    public static final int CAPACITY_PER_ABSORB = 2;
    public static final int MAX_CAPACITY = ManaStage.ARCHMAGE.minCapacity();

    private Mana() {}

    public static ManaData get(Player player) {
        return player.getData(ModAttachments.MANA);
    }

    public static void set(Player player, ManaData data) {
        if (!data.equals(get(player))) {
            player.setData(ModAttachments.MANA, data);
        }
    }

    /** Chance (0..1) that a broken block yields raw mana for someone with this much experience. */
    public static float findChance(int experience) {
        return Math.min(BASE_FIND_CHANCE + FIND_CHANCE_PER_EXPERIENCE * experience, MAX_FIND_CHANCE);
    }

    /**
     * Damage (in half hearts) dealt by mana the body could not hold. The same overflow hurts
     * less and less as capacity grows, i.e. as the body gets used to mana.
     */
    public static float overflowDamage(int overflow, int capacity) {
        return overflow <= 0 ? 0.0F : overflow * 4.0F / (capacity + 10.0F);
    }

    /** Called when a player finds raw mana in a block. */
    public static void onRawManaFound(Player player) {
        ManaData data = get(player);
        set(player, new ManaData(data.mana(), data.capacity(), data.experience() + EXPERIENCE_PER_FIND));
    }

    /**
     * Takes one piece of refined mana into the body: capacity grows a little, the mana is
     * stored, and whatever does not fit is lost and reported as overflow.
     */
    public static AbsorbResult absorb(Player player) {
        ManaData before = get(player);
        int capacity = Math.min(before.capacity() + CAPACITY_PER_ABSORB, MAX_CAPACITY);
        int wanted = before.mana() + MANA_PER_REFINED;
        int mana = Math.min(wanted, capacity);
        int overflow = wanted - mana;
        ManaData after = new ManaData(mana, capacity, before.experience() + EXPERIENCE_PER_ABSORB);
        set(player, after);
        return new AbsorbResult(overflow, overflowDamage(overflow, capacity), before.stage(), after.stage());
    }

    public record AbsorbResult(int overflow, float damage, ManaStage stageBefore, ManaStage stageAfter) {
        public boolean stageChanged() {
            return stageBefore != stageAfter;
        }
    }
}
