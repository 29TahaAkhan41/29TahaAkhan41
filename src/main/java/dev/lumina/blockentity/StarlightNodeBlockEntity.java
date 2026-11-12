package dev.lumina.blockentity;

import dev.lumina.starlight.Beam;
import dev.lumina.starlight.LinkResult;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientGamePacketListener;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.util.Mth;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.state.BlockState;

/**
 * Base of every block that can hold starlight. A node has a buffer, and may aim beams at other
 * nodes; every {@link #TRANSFER_INTERVAL} ticks it pushes part of its buffer down those beams.
 */
public abstract class StarlightNodeBlockEntity extends BlockEntity {
    public static final int TRANSFER_INTERVAL = 10;
    private static final int SYNC_STEPS = 16;

    protected float starlight;
    private final List<BlockPos> targets = new ArrayList<>();
    private int lastSyncedStep = -1;

    protected StarlightNodeBlockEntity(BlockEntityType<?> type, BlockPos pos, BlockState state) {
        super(type, pos, state);
    }

    // ---- Per-node tuning --------------------------------------------------

    public abstract float getCapacity();

    /** How many beams this node can emit. 0 means it only receives. */
    public abstract int getMaxTargets();

    /** Starlight pushed out per transfer cycle, shared between all beams. */
    public abstract float getTransferRate();

    // ---- Buffer -----------------------------------------------------------

    public float getStarlight() {
        return starlight;
    }

    public float getFillRatio() {
        return Mth.clamp(starlight / getCapacity(), 0.0F, 1.0F);
    }

    public int getComparatorSignal() {
        return starlight <= 0.0F ? 0 : 1 + Mth.floor(getFillRatio() * 14.0F);
    }

    /** Adds starlight to the buffer and returns how much actually fitted. */
    public float receive(float amount) {
        float accepted = Mth.clamp(amount, 0.0F, getCapacity() - starlight);
        if (accepted > 0.0F) {
            starlight += accepted;
            setChanged();
        }
        return accepted;
    }

    /** Removes up to {@code amount} and returns how much was taken. */
    protected float drain(float amount) {
        float taken = Mth.clamp(amount, 0.0F, starlight);
        if (taken > 0.0F) {
            starlight -= taken;
            if (starlight < 1.0E-3F) {
                starlight = 0.0F;
            }
            setChanged();
        }
        return taken;
    }

    // ---- Links ------------------------------------------------------------

    public List<BlockPos> getTargets() {
        return Collections.unmodifiableList(targets);
    }

    public LinkResult link(BlockPos target) {
        if (level == null || getMaxTargets() <= 0) {
            return LinkResult.CANNOT_EMIT;
        }
        if (target.equals(worldPosition)) {
            return LinkResult.SAME_BLOCK;
        }
        if (targets.contains(target)) {
            return LinkResult.ALREADY_LINKED;
        }
        if (!(level.getBlockEntity(target) instanceof StarlightNodeBlockEntity other)) {
            return LinkResult.NOT_A_NODE;
        }
        if (other.targets.contains(worldPosition)) {
            return LinkResult.WOULD_LOOP;
        }
        if (!Beam.inRange(worldPosition, target)) {
            return LinkResult.TOO_FAR;
        }
        if (!Beam.hasLineOfSight(level, worldPosition, target)) {
            return LinkResult.NO_LINE_OF_SIGHT;
        }
        if (targets.size() >= getMaxTargets()) {
            return LinkResult.NO_FREE_OUTPUT;
        }
        targets.add(target.immutable());
        setChanged();
        sync();
        return LinkResult.LINKED;
    }

    /** Drops every outgoing beam. Returns how many were removed. */
    public int clearLinks() {
        int removed = targets.size();
        if (removed > 0) {
            targets.clear();
            setChanged();
            sync();
        }
        return removed;
    }

    // ---- Ticking ----------------------------------------------------------

    public final void serverTick() {
        if (level == null) {
            return;
        }
        tickNode();
        if (!targets.isEmpty() && (level.getGameTime() + worldPosition.asLong()) % TRANSFER_INTERVAL == 0) {
            transmit();
        }
        int step = Mth.ceil(getFillRatio() * SYNC_STEPS);
        if (step != lastSyncedStep) {
            lastSyncedStep = step;
            sync();
            level.updateNeighbourForOutputSignal(worldPosition, getBlockState().getBlock());
        }
    }

    /** Node specific work done every server tick (collecting, infusing, ...). */
    protected void tickNode() {
    }

    private void transmit() {
        if (starlight <= 0.0F) {
            return;
        }
        List<StarlightNodeBlockEntity> reachable = new ArrayList<>(targets.size());
        for (BlockPos target : targets) {
            StarlightNodeBlockEntity node = resolveTarget(target);
            if (node != null) {
                reachable.add(node);
            }
        }
        if (reachable.isEmpty()) {
            return;
        }
        float share = Math.min(starlight, getTransferRate()) / reachable.size();
        for (StarlightNodeBlockEntity node : reachable) {
            float efficiency = Beam.efficiency(worldPosition, node.getBlockPos());
            if (efficiency <= 0.0F) {
                continue;
            }
            float delivered = node.receive(share * efficiency);
            drain(delivered / efficiency);
        }
    }

    /** The node a beam ends at, or null while the beam is broken, blocked or unloaded. */
    private StarlightNodeBlockEntity resolveTarget(BlockPos target) {
        if (level == null || !level.isLoaded(target) || !Beam.inRange(worldPosition, target)) {
            return null;
        }
        if (!(level.getBlockEntity(target) instanceof StarlightNodeBlockEntity node)) {
            return null;
        }
        return Beam.hasLineOfSight(level, worldPosition, target) ? node : null;
    }

    // ---- Persistence & sync ----------------------------------------------

    protected void sync() {
        if (level != null && !level.isClientSide) {
            level.sendBlockUpdated(worldPosition, getBlockState(), getBlockState(), Block.UPDATE_CLIENTS);
        }
    }

    @Override
    protected void saveAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.saveAdditional(tag, registries);
        tag.putFloat("Starlight", starlight);
        long[] packed = new long[targets.size()];
        for (int i = 0; i < packed.length; i++) {
            packed[i] = targets.get(i).asLong();
        }
        tag.putLongArray("Targets", packed);
    }

    @Override
    protected void loadAdditional(CompoundTag tag, HolderLookup.Provider registries) {
        super.loadAdditional(tag, registries);
        starlight = tag.getFloat("Starlight");
        targets.clear();
        for (long packed : tag.getLongArray("Targets")) {
            targets.add(BlockPos.of(packed));
        }
    }

    @Override
    public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
        return saveWithoutMetadata(registries);
    }

    @Override
    public Packet<ClientGamePacketListener> getUpdatePacket() {
        return ClientboundBlockEntityDataPacket.create(this);
    }
}
