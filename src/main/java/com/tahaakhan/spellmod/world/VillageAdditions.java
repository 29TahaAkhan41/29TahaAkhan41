package com.tahaakhan.spellmod.world;

import com.mojang.datafixers.util.Pair;
import com.tahaakhan.spellmod.SpellMod;
import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.Identifier;
import net.minecraft.world.level.levelgen.structure.pools.StructurePoolElement;
import net.minecraft.world.level.levelgen.structure.pools.StructureTemplatePool;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;

/**
 * Adds a wizard house to the house pools of every kind of village, each built from the materials
 * of that village type. At most one is built per village.
 */
@EventBusSubscriber(modid = SpellMod.MODID)
public final class VillageAdditions {
    public static final List<String> VILLAGE_TYPES = List.of("plains", "desert", "savanna", "snowy", "taiga");
    /**
     * How often the wizard house is picked compared to the other houses (the vanilla house
     * pools have a total weight of about 70-90). Higher means fewer villages without a wizard
     * house, but more plots left empty, because only one wizard house is built per village.
     */
    public static final int WEIGHT = 3;

    private VillageAdditions() {}

    /** The structure file of the wizard house for a village type (see tools/make_wizard_houses.py). */
    public static Identifier wizardHouse(String villageType) {
        return SpellMod.id("village/wizard_house_" + villageType);
    }

    public static Identifier housePool(String villageType) {
        return Identifier.withDefaultNamespace("village/" + villageType + "/houses");
    }

    @SubscribeEvent
    static void onServerAboutToStart(ServerAboutToStartEvent event) {
        Registry<StructureTemplatePool> pools = event.getServer().registryAccess().lookupOrThrow(Registries.TEMPLATE_POOL);
        for (String type : VILLAGE_TYPES) {
            StructureTemplatePool pool = pools.getValue(housePool(type));
            if (pool != null && !contains(pool)) {
                add(pool, wizardHouse(type));
            }
        }
    }

    public static boolean contains(StructureTemplatePool pool) {
        return pool.rawTemplates.stream().anyMatch(entry -> entry.getFirst() instanceof UniqueVillageHouseElement);
    }

    private static void add(StructureTemplatePool pool, Identifier template) {
        StructurePoolElement house = new UniqueVillageHouseElement(template);
        // The pool keeps both a weighted list and a flat list with one entry per weight point.
        List<Pair<StructurePoolElement, Integer>> raw = new ArrayList<>(pool.rawTemplates);
        raw.add(Pair.of(house, WEIGHT));
        pool.rawTemplates = raw;
        for (int i = 0; i < WEIGHT; i++) {
            pool.templates.add(house);
        }
    }
}
