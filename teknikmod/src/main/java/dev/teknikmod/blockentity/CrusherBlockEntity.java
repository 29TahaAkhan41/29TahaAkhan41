package dev.teknikmod.blockentity;

import dev.teknikmod.ModRegistry;
import dev.teknikmod.menu.ProcessingMenu;
import dev.teknikmod.recipe.CrushingRecipe;
import net.minecraft.core.BlockPos;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;

/** teknikmod:crushing tariflerini isler. */
public class CrusherBlockEntity extends ProcessingBlockEntity {
    private final RecipeManager.CachedCheck<SingleRecipeInput, CrushingRecipe> check =
            RecipeManager.createCheck(ModRegistry.CRUSHING.get());

    public CrusherBlockEntity(BlockPos pos, BlockState state) {
        super(ModRegistry.CRUSHER_BE.get(), pos, state);
    }

    @Override
    protected Job findJob(Level level, ItemStack input) {
        SingleRecipeInput recipeInput = new SingleRecipeInput(input);
        return check.getRecipeFor(recipeInput, level)
                .map(h -> new Job(h.value().assemble(recipeInput, level.registryAccess()), h.value().time()))
                .orElse(null);
    }

    @Override
    protected MenuType<ProcessingMenu> menuType() {
        return ModRegistry.CRUSHER_MENU.get();
    }
}
