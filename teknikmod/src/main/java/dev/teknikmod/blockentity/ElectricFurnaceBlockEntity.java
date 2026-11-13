package dev.teknikmod.blockentity;

import dev.teknikmod.ModRegistry;
import dev.teknikmod.menu.ProcessingMenu;
import net.minecraft.core.BlockPos;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/** Normal firin tariflerini (baska modlarinkiler dahil) elektrikle pisirir. */
public class ElectricFurnaceBlockEntity extends ProcessingBlockEntity {
    private final RecipeManager.CachedCheck<SingleRecipeInput, SmeltingRecipe> check =
            RecipeManager.createCheck(RecipeType.SMELTING);

    public ElectricFurnaceBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.ELECTRIC_FURNACE_BE.get(), pos, state);
    }

    @Override
    protected Job findJob(Level level, ItemStack input) {
        SingleRecipeInput recipeInput = new SingleRecipeInput(input);
        return check.getRecipeFor(recipeInput, level)
                .map(h -> new Job(h.value().assemble(recipeInput, level.registryAccess()), h.value().getCookingTime()))
                .orElse(null);
    }

    @Override
    protected MenuType<ProcessingMenu> menuType() {
        return ModRegistry.ELECTRIC_FURNACE_MENU.get();
    }
}
