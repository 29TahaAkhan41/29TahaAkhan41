package dev.teknikmod;

import dev.teknikmod.blockentity.BatteryBlockEntity;
import dev.teknikmod.blockentity.CableBlockEntity;
import dev.teknikmod.blockentity.CoalGeneratorBlockEntity;
import dev.teknikmod.blockentity.ProcessingBlockEntity;
import dev.teknikmod.blockentity.SolarPanelBlockEntity;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.capabilities.RegisterCapabilitiesEvent;

@Mod(TeknikMod.MODID)
public class TeknikMod {
    public static final String MODID = "teknikmod";

    public TeknikMod(IEventBus modBus) {
        ModRegistry.register(modBus);
        modBus.addListener(TeknikMod::registerCapabilities);
    }

    private static void registerCapabilities(RegisterCapabilitiesEvent event) {
        event.registerBlockEntity(Capabilities.EnergyStorage.BLOCK, ModRegistry.COAL_GENERATOR_BE.get(),
                CoalGeneratorBlockEntity::getEnergy);
        event.registerBlockEntity(Capabilities.ItemHandler.BLOCK, ModRegistry.COAL_GENERATOR_BE.get(),
                (be, side) -> be.getItems());
        event.registerBlockEntity(Capabilities.EnergyStorage.BLOCK, ModRegistry.SOLAR_PANEL_BE.get(),
                SolarPanelBlockEntity::getEnergy);
        event.registerBlockEntity(Capabilities.EnergyStorage.BLOCK, ModRegistry.BATTERY_BE.get(),
                BatteryBlockEntity::getEnergy);
        for (var type : java.util.List.of(ModRegistry.ELECTRIC_FURNACE_BE.get(), ModRegistry.CRUSHER_BE.get())) {
            event.registerBlockEntity(Capabilities.EnergyStorage.BLOCK, type, ProcessingBlockEntity::getEnergy);
            event.registerBlockEntity(Capabilities.ItemHandler.BLOCK, type, ProcessingBlockEntity::getAutomationItems);
        }
        event.registerBlockEntity(Capabilities.EnergyStorage.BLOCK, ModRegistry.CABLE_BE.get(),
                CableBlockEntity::getEnergy);
    }
}
