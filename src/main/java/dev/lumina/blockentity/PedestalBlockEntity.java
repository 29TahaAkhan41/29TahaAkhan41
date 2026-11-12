package dev.lumina.blockentity;

import dev.lumina.Lumina;
import dev.lumina.recipe.InfusionRecipe;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.IItemHandler;

/** Holds one item and pours received starlight into it until the infusion recipe completes. */
public class PedestalBlockEntity extends StarlightNodeBlockEntity {
    /** Most starlight the pedestal can work into the item per tick. */
    public static final float INFUSE_RATE = 8.0F;

    private ItemStack item = ItemStack.EMPTY;
    private float progress;
    private final RecipeManager.CachedCheck<SingleRecipeInput, InfusionRecipe> recipeCheck =
            RecipeManager.createCheck(Lumina.INFUSION_TYPE.get());
    private final IItemHandler itemHandler = new PedestalItemHandler();

    public PedestalBlockEntity(BlockPos pos, BlockState state) {
        super(Lumina.PEDESTAL_BE.get(), pos, state);
    }

    @Override
    public float getCapacity() {
        return 400.0F;
    }

    @Override
    public int getMaxTargets() {
        return 0;
    }

    @Override
    public float getTransferRate() {
        return 0.0F;
    }

    public ItemStack getItem() {
        return item;
    }

    public void setItem(ItemStack stack) {
        item = stack;
        progress = 0.0F;
        setChanged();
        sync();
    }

    public float getProgress() {
        return progress;
    }

    public IItemHandler getItemHandler() {
        return itemHandler;
    }

    public Optional<RecipeHolder<InfusionRecipe>> findRecipe(ItemStack stack) {
        if (level == null || stack.isEmpty()) {
            return Optional.empty();
        }
        return recipeCheck.getRecipeFor(new SingleRecipeInput(stack), level);
    }

    /** Starlight still needed to finish the current item, or 0 when nothing is being infused. */
    public int getRequiredStarlight() {
        return findRecipe(item).map(holder -> holder.value().starlight()).orElse(0);
    }

    @Override
    protected void tickNode() {
        if (item.isEmpty() || level == null) {
            return;
        }
        Optional<RecipeHolder<InfusionRecipe>> recipe = findRecipe(item);
        if (recipe.isEmpty()) {
            return;
        }
        int cost = recipe.get().value().starlight();
        progress += drain(Math.min(INFUSE_RATE, cost - progress));
        if (progress >= cost) {
            item = recipe.get().value().assemble(new SingleRecipeInput(item), level.registryAccess());
            progress = 0.0F;
            setChanged();
            sync();
            level.playSound(null, worldPosition, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.2F);
            if (level instanceof ServerLevel server) {
                server.sendParticles(ParticleTypes.END_ROD, worldPosition.getX() + 0.5,
                        worldPosition.getY() + 1.2, worldPosition.getZ() + 0.5, 12, 0.15, 0.15, 0.15, 0.03);
            }
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.put("Item", item.saveOptional(registries));
        tag.putFloat("Progress", progress);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        item = ItemStack.parseOptional(registries, tag.getCompound("Item"));
        progress = tag.getFloat("Progress");
    }

    /** Automation view: accepts one infusable item, hands back only finished items. */
    private class PedestalItemHandler implements IItemHandler {
        @Override
        public int getSlots() {
            return 1;
        }

        @Override
        public ItemStack getStackInSlot(int slot) {
            return item;
        }

        @Override
        public ItemStack insertItem(int slot, ItemStack stack, boolean simulate) {
            if (stack.isEmpty() || !item.isEmpty() || !isItemValid(slot, stack)) {
                return stack;
            }
            if (!simulate) {
                setItem(stack.copyWithCount(1));
            }
            return stack.copyWithCount(stack.getCount() - 1);
        }

        @Override
        public ItemStack extractItem(int slot, int amount, boolean simulate) {
            if (amount <= 0 || item.isEmpty() || findRecipe(item).isPresent()) {
                return ItemStack.EMPTY;
            }
            ItemStack out = item.copy();
            if (!simulate) {
                setItem(ItemStack.EMPTY);
            }
            return out;
        }

        @Override
        public int getSlotLimit(int slot) {
            return 1;
        }

        @Override
        public boolean isItemValid(int slot, ItemStack stack) {
            return findRecipe(stack).isPresent();
        }
    }
}
