package com.tahaakhan.spellmod.block;

import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.mana.ManaData;
import com.tahaakhan.spellmod.menu.ManaTableMenu;
import com.tahaakhan.spellmod.registry.ModBlockEntities;
import com.tahaakhan.spellmod.registry.ModItems;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.NonNullList;
import net.minecraft.core.UUIDUtil;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.ContainerHelper;
import net.minecraft.world.WorldlyContainer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.ContainerData;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.entity.BaseContainerBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.ValueInput;
import net.minecraft.world.level.storage.ValueOutput;
import org.jspecify.annotations.Nullable;

/**
 * Refines raw mana, one piece at a time. Each piece costs one eye of ender, takes a time that
 * depends on how much the player has refined before, and may be destroyed depending on the
 * player's affinity for mana. Both are decided for the player who pressed the button.
 */
public class ManaTableBlockEntity extends BaseContainerBlockEntity implements WorldlyContainer {
    public static final int SLOT_INPUT = 0;
    public static final int SLOT_FUEL = 1;
    public static final int SLOT_OUTPUT = 2;
    public static final int SLOT_COUNT = 3;

    public static final int DATA_PROGRESS = 0;
    public static final int DATA_TOTAL = 1;
    /** Loss chance of the piece being refined, in 1/1000. */
    public static final int DATA_LOSS = 2;
    public static final int DATA_RUNNING = 3;
    public static final int DATA_COUNT = 4;

    private static final int[] SLOTS_UP = {SLOT_INPUT};
    private static final int[] SLOTS_SIDE = {SLOT_FUEL};
    private static final int[] SLOTS_DOWN = {SLOT_OUTPUT};

    private NonNullList<ItemStack> items = NonNullList.withSize(SLOT_COUNT, ItemStack.EMPTY);
    private int progress;
    private int total = Mana.MAX_REFINE_TICKS;
    private int lossPermille = Math.round(Mana.MAX_LOSS_CHANCE * 1000);
    private boolean running;
    private @Nullable UUID owner;

    private final ContainerData data = new ContainerData() {
        @Override
        public int get(int id) {
            return switch (id) {
                case DATA_PROGRESS -> progress;
                case DATA_TOTAL -> total;
                case DATA_LOSS -> lossPermille;
                case DATA_RUNNING -> running ? 1 : 0;
                default -> 0;
            };
        }

        @Override
        public void set(int id, int value) {}

        @Override
        public int getCount() {
            return DATA_COUNT;
        }
    };

    public ManaTableBlockEntity(BlockPos pos, BlockState state) {
        super(ModBlockEntities.MANA_TABLE.get(), pos, state);
    }

    public static boolean isInput(ItemStack stack) {
        return stack.is(ModItems.RAW_MANA.get());
    }

    public static boolean isFuel(ItemStack stack) {
        return stack.is(Items.ENDER_EYE);
    }

    public boolean isRunning() {
        return running;
    }

    public int totalTicks() {
        return total;
    }

    public int lossPermille() {
        return lossPermille;
    }

    /**
     * The "Refine" button. Starts refining everything in the input slot on behalf of this player.
     *
     * @return false if already running or if raw mana, fuel or output space is missing
     */
    public boolean start(ServerPlayer player) {
        if (running || !(level instanceof ServerLevel serverLevel)) {
            return false;
        }
        owner = player.getUUID();
        return beginNext(serverLevel);
    }

    private boolean canBegin() {
        ItemStack output = items.get(SLOT_OUTPUT);
        return isInput(items.get(SLOT_INPUT)) && isFuel(items.get(SLOT_FUEL))
                && (output.isEmpty() || output.is(ModItems.REFINED_MANA.get()) && output.getCount() < output.getMaxStackSize());
    }

    /** Takes one raw mana and one eye of ender and starts the timer. */
    private boolean beginNext(ServerLevel level) {
        running = false;
        progress = 0;
        if (!canBegin()) {
            setChanged();
            return false;
        }
        // If the owner has logged off, keep going with the numbers of their last piece.
        ServerPlayer player = owner == null ? null : level.getServer().getPlayerList().getPlayer(owner);
        if (player != null) {
            ManaData mana = Mana.get(player);
            total = Mana.refineTicks(mana.refined());
            lossPermille = Math.round(Mana.lossChance(mana) * 1000);
            Mana.onRefineStarted(player);
        }
        items.get(SLOT_INPUT).shrink(1);
        items.get(SLOT_FUEL).shrink(1);
        running = true;
        setChanged();
        return true;
    }

    public static void serverTick(ServerLevel level, BlockPos pos, BlockState state, ManaTableBlockEntity table) {
        if (!table.running) {
            return;
        }
        table.progress++;
        if (table.progress >= table.total) {
            table.complete(level, level.getRandom().nextInt(1000));
        }
        table.setChanged();
    }

    /**
     * Finishes the piece being refined.
     *
     * @param roll a random number in [0, 1000); the mana is destroyed when it is below the loss chance
     */
    public void complete(ServerLevel level, int roll) {
        if (!running) {
            return;
        }
        BlockPos pos = getBlockPos();
        double x = pos.getX() + 0.5;
        double y = pos.getY() + 0.85;
        double z = pos.getZ() + 0.5;
        if (roll < lossPermille) {
            level.sendParticles(ParticleTypes.LARGE_SMOKE, x, y, z, 12, 0.2, 0.1, 0.2, 0.01);
            level.playSound(null, pos, SoundEvents.FIRE_EXTINGUISH, SoundSource.BLOCKS, 0.7F, 1.3F);
        } else {
            ItemStack output = items.get(SLOT_OUTPUT);
            if (output.isEmpty()) {
                items.set(SLOT_OUTPUT, new ItemStack(ModItems.REFINED_MANA.get()));
            } else {
                output.grow(1);
            }
            level.sendParticles(ParticleTypes.END_ROD, x, y, z, 12, 0.2, 0.1, 0.2, 0.03);
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.2F);
        }
        beginNext(level);
    }

    @Override
    protected Component getDefaultName() {
        return Component.translatable("container.spellmod.mana_table");
    }

    @Override
    protected AbstractContainerMenu createMenu(int containerId, Inventory inventory) {
        return new ManaTableMenu(containerId, inventory, this, data);
    }

    @Override
    public int getContainerSize() {
        return SLOT_COUNT;
    }

    @Override
    protected NonNullList<ItemStack> getItems() {
        return items;
    }

    @Override
    protected void setItems(NonNullList<ItemStack> items) {
        this.items = items;
    }

    @Override
    public boolean canPlaceItem(int slot, ItemStack stack) {
        return switch (slot) {
            case SLOT_INPUT -> isInput(stack);
            case SLOT_FUEL -> isFuel(stack);
            default -> false;
        };
    }

    // Hoppers: raw mana in from the top, eyes of ender from the sides, refined mana out of the bottom.
    @Override
    public int[] getSlotsForFace(Direction direction) {
        return direction == Direction.UP ? SLOTS_UP : direction == Direction.DOWN ? SLOTS_DOWN : SLOTS_SIDE;
    }

    @Override
    public boolean canPlaceItemThroughFace(int slot, ItemStack stack, @Nullable Direction direction) {
        return canPlaceItem(slot, stack);
    }

    @Override
    public boolean canTakeItemThroughFace(int slot, ItemStack stack, Direction direction) {
        return slot == SLOT_OUTPUT;
    }

    @Override
    protected void loadAdditional(ValueInput input) {
        super.loadAdditional(input);
        items = NonNullList.withSize(SLOT_COUNT, ItemStack.EMPTY);
        ContainerHelper.loadAllItems(input, items);
        progress = input.getIntOr("progress", 0);
        total = input.getIntOr("total", Mana.MAX_REFINE_TICKS);
        lossPermille = input.getIntOr("loss", Math.round(Mana.MAX_LOSS_CHANCE * 1000));
        running = input.getBooleanOr("running", false);
        owner = input.read("owner", UUIDUtil.CODEC).orElse(null);
    }

    @Override
    protected void saveAdditional(ValueOutput output) {
        super.saveAdditional(output);
        ContainerHelper.saveAllItems(output, items);
        output.putInt("progress", progress);
        output.putInt("total", total);
        output.putInt("loss", lossPermille);
        output.putBoolean("running", running);
        if (owner != null) {
            output.store("owner", UUIDUtil.CODEC, owner);
        }
    }
}
