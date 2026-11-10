package com.tahaakhan.spellmod.item;

import com.tahaakhan.spellmod.mana.Mana;
import com.tahaakhan.spellmod.registry.ModDataComponents;
import com.tahaakhan.spellmod.spell.Spell;
import java.util.function.Consumer;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
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

/**
 * Right click: cast the selected spell. Sneak + right click: switch to the next spell.
 */
public class WandItem extends Item {
    public WandItem(Properties properties) {
        super(properties);
    }

    public static Spell getSpell(ItemStack stack) {
        return stack.getOrDefault(ModDataComponents.SELECTED_SPELL, Spell.FIREBALL);
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(level instanceof ServerLevel serverLevel) || !(player instanceof ServerPlayer serverPlayer)) {
            return InteractionResult.SUCCESS;
        }

        Spell spell = getSpell(stack);
        if (player.isShiftKeyDown()) {
            Spell next = spell.next();
            stack.set(ModDataComponents.SELECTED_SPELL, next);
            level.playSound(null, player.getX(), player.getY(), player.getZ(),
                    SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, 0.5F, 1.4F);
            player.sendOverlayMessage(Component.translatable("message.spellmod.selected", next.displayName(), next.manaCost()));
            return InteractionResult.SUCCESS_SERVER;
        }

        boolean free = player.hasInfiniteMaterials();
        if (!free && Mana.get(player) < spell.manaCost()) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.no_mana", spell.manaCost()).withStyle(ChatFormatting.RED));
            return InteractionResult.FAIL;
        }
        if (!spell.cast(serverLevel, serverPlayer)) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.failed").withStyle(ChatFormatting.GRAY));
            return InteractionResult.FAIL;
        }
        if (!free) {
            Mana.add(player, -spell.manaCost());
        }
        player.getCooldowns().addCooldown(stack, spell.cooldownTicks());
        return InteractionResult.SUCCESS_SERVER;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, TooltipDisplay display, Consumer<Component> builder, TooltipFlag flag) {
        Spell spell = getSpell(stack);
        builder.accept(Component.translatable("tooltip.spellmod.spell", spell.displayName(), spell.manaCost()).withStyle(ChatFormatting.GRAY));
        builder.accept(Component.translatable("tooltip.spellmod.wand_hint").withStyle(ChatFormatting.DARK_GRAY));
    }
}
