package dev.teknikmod.energy;

import net.neoforged.neoforge.energy.EnergyStorage;
import net.neoforged.neoforge.energy.IEnergyStorage;

/** Degisikliklerde haber veren ve tek yonlu gorunumler sunan enerji deposu. */
public class ModEnergyStorage extends EnergyStorage {
    private final Runnable onChange;

    public ModEnergyStorage(int capacity, int maxReceive, int maxExtract, Runnable onChange) {
        super(capacity, maxReceive, maxExtract);
        this.onChange = onChange;
    }

    public void setEnergy(int value) {
        this.energy = Math.max(0, Math.min(capacity, value));
    }

    /** Cihazin kendi urettigi enerjiyi ekler (maxReceive sinirini yok sayar). */
    public int generate(int amount) {
        int added = Math.min(capacity - energy, amount);
        if (added > 0) {
            energy += added;
            onChange.run();
        }
        return added;
    }

    @Override
    public int receiveEnergy(int toReceive, boolean simulate) {
        int r = super.receiveEnergy(toReceive, simulate);
        if (r > 0 && !simulate) onChange.run();
        return r;
    }

    @Override
    public int extractEnergy(int toExtract, boolean simulate) {
        int r = super.extractEnergy(toExtract, simulate);
        if (r > 0 && !simulate) onChange.run();
        return r;
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
