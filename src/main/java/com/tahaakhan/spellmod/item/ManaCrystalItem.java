package com.tahaakhan.spellmod.item;

import com.tahaakhan.spellmod.mana.Mana;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.component.TooltipDisplay;
import net.minecraft.world.level.Level;

/** Consumed on right click to restore mana instantly. */
public class ManaCrystalItem extends Item {
    public static final int RESTORE_AMOUNT = 50;

    public ManaCrystalItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        if (Mana.get(player) >= Mana.MAX) {
            return InteractionResult.FAIL;
        }
        Mana.add(player, RESTORE_AMOUNT);
        player.getItemInHand(hand).consume(1, player);
        level.playSound(null, player.getX(), player.getY(), player.getZ(),
                SoundEvents.AMETHYST_BLOCK_CHIME, SoundSource.PLAYERS, 1.0F, 1.5F);
        return InteractionResult.SUCCESS_SERVER;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> builder, TooltipFlag flag) {
        builder.accept(Component.translatable("tooltip.spellmod.mana_crystal", RESTORE_AMOUNT).withStyle(ChatFormatting.GRAY));
    }
}
