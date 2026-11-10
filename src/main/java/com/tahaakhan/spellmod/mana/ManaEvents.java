package com.tahaakhan.spellmod.mana;

import com.mojang.brigadier.Command;
import com.tahaakhan.spellmod.SpellMod;
import com.tahaakhan.spellmod.registry.ModItems;
import net.minecraft.ChatFormatting;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;
import net.neoforged.neoforge.event.level.block.BreakBlockEvent;

@EventBusSubscriber(modid = SpellMod.MODID)
public final class ManaEvents {
    private ManaEvents() {}

    @SubscribeEvent(priority = EventPriority.LOWEST)
    static void onBlockBreak(BreakBlockEvent event) {
        if (event.isCanceled() || !(event.getLevel() instanceof ServerLevel level)) {
            return;
        }
        Player player = event.getPlayer();
        tryDropRawMana(level, event.getPos(), event.getState(), player, player.getRandom().nextFloat());
    }

    /**
     * @param roll a random number in [0, 1); raw mana drops when it is below the player's find chance
     * @return whether raw mana dropped
     */
    public static boolean tryDropRawMana(ServerLevel level, BlockPos pos, BlockState state, Player player, float roll) {
        // Creative players and blocks that break instantly (grass, flowers, torches...) never yield mana.
        if (player.hasInfiniteMaterials() || state.getDestroySpeed(level, pos) <= 0.0F) {
            return false;
        }
        ManaData data = Mana.get(player);
        if (roll >= Mana.findChance(data.experience())) {
            return false;
        }
        Block.popResource(level, pos, new ItemStack(ModItems.RAW_MANA.get()));
        level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.BLOCKS, 1.0F, 1.6F);
        Mana.onRawManaFound(player);
        if (data.experience() == 0) {
            player.sendSystemMessage(Component.translatable("message.spellmod.first_raw_mana").withStyle(ChatFormatting.AQUA));
        }
        return true;
    }

    /** {@code /mana}: shows your own mana state. */
    @SubscribeEvent
    static void registerCommands(RegisterCommandsEvent event) {
        event.getDispatcher().register(Commands.literal("mana").executes(context -> {
            ServerPlayer player = context.getSource().getPlayerOrException();
            ManaData data = Mana.get(player);
            String chance = String.format("%.2f", Mana.findChance(data.experience()) * 100.0F);
            context.getSource().sendSuccess(() -> Component.translatable("message.spellmod.status",
                    data.stage().displayName(), data.mana(), data.capacity(), data.experience(), chance), false);
            return Command.SINGLE_SUCCESS;
        }));
    }
}
