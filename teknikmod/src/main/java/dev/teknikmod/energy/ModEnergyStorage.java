package dev.teknikmod.energy;

import net.neoforged.neoforge.energy.EnergyStorage;
import net.neoforged.neoforge.energy.IEnergyStorage;

import java.util.function.LongSupplier;

/** Degisikliklerde haber veren ve tek yonlu gorunumler sunan enerji deposu. */
public class ModEnergyStorage extends EnergyStorage {
    private final Runnable onChange;
    /** Sonsuz depo: hep doludur, cekilen enerji eksilmez, enerji kabul etmez. */
    private final boolean infinite;
    /** Oyun zamani; giris/cikis sinirlarini cagri basina degil tick basina uygulamak icin. */
    private final LongSupplier clock;
    private long lastTick = Long.MIN_VALUE;
    private int receivedThisTick, extractedThisTick;

    public ModEnergyStorage(int capacity, int maxReceive, int maxExtract, Runnable onChange, boolean infinite, LongSupplier clock) {
        super(capacity, maxReceive, maxExtract);
        this.onChange = onChange;
        this.infinite = infinite;
        this.clock = clock;
        if (infinite) this.energy = capacity;
    }

    private void rollTick() {
        long now = clock.getAsLong();
        if (now != lastTick) {
            lastTick = now;
            receivedThisTick = extractedThisTick = 0;
        }
    }

    public void setEnergy(int value) {
        if (infinite) return;
        this.energy = Math.max(0, Math.min(capacity, value));
    }

    /** Cihazin kendi urettigi enerjiyi ekler (maxReceive sinirini yok sayar). */
    public int generate(int amount) {
        if (infinite) return 0;
        int added = Math.min(capacity - energy, amount);
        if (added > 0) {
            energy += added;
            onChange.run();
        }
        return added;
    }

    @Override
    public int receiveEnergy(int toReceive, boolean simulate) {
        if (infinite) return 0;
        rollTick();
        int r = super.receiveEnergy(Math.min(toReceive, maxReceive - receivedThisTick), simulate);
        if (r > 0 && !simulate) {
            receivedThisTick += r;
            onChange.run();
        }
        return r;
    }

    @Override
    public int extractEnergy(int toExtract, boolean simulate) {
        if (infinite) return Math.max(0, Math.min(maxExtract, toExtract));
        rollTick();
        int r = super.extractEnergy(Math.min(toExtract, maxExtract - extractedThisTick), simulate);
        if (r > 0 && !simulate) {
            extractedThisTick += r;
            onChange.run();
        }
        return r;
    }

    @Override
    public boolean canReceive() {
        return !infinite && super.canReceive();
    }

    /** Sadece enerji cekilebilen gorunum. */
    public IEnergyStorage outputOnly() {
        return new View(false, true);
    }

    /** Sadece enerji verilebilen gorunum. */
    public IEnergyStorage inputOnly() {
        return new View(true, false);
    }

    private final class View implements IEnergyStorage {
        private final boolean in, out;

        View(boolean in, boolean out) {
            this.in = in;
            this.out = out;
        }

        @Override public int receiveEnergy(int a, boolean sim) { return in ? ModEnergyStorage.this.receiveEnergy(a, sim) : 0; }
        @Override public int extractEnergy(int a, boolean sim) { return out ? ModEnergyStorage.this.extractEnergy(a, sim) : 0; }
        @Override public int getEnergyStored() { return ModEnergyStorage.this.getEnergyStored(); }
        @Override public int getMaxEnergyStored() { return ModEnergyStorage.this.getMaxEnergyStored(); }
        @Override public boolean canExtract() { return out && ModEnergyStorage.this.canExtract(); }
        @Override public boolean canReceive() { return in && ModEnergyStorage.this.canReceive(); }
    }
}
