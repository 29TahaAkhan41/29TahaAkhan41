package com.tahaakhan.spellmod.item;

import com.tahaakhan.spellmod.registry.ModDataComponents;
import com.tahaakhan.spellmod.registry.ModItems;
import com.tahaakhan.spellmod.spell.Spell;
import com.tahaakhan.spellmod.spell.SpellCasting;
import com.tahaakhan.spellmod.spell.Spells;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.jspecify.annotations.Nullable;

/** A book holding one spell. Right click to read it and learn the spell; the book is used up. */
public class SpellBookItem extends Item {
    public SpellBookItem(Properties properties) {
        super(properties);
    }

    public static ItemStack of(Spell spell) {
        ItemStack stack = new ItemStack(ModItems.SPELL_BOOK.get());
        stack.set(ModDataComponents.SPELL, spell.id());
        return stack;
    }

    public static @Nullable Spell getSpell(ItemStack stack) {
        Identifier id = stack.get(ModDataComponents.SPELL);
        return id == null ? null : Spells.get(id);
    }

    @Override
    public Component getName(ItemStack stack) {
        Spell spell = getSpell(stack);
        return spell == null ? super.getName(stack) : Component.translatable("item.spellmod.spell_book.named", spell.displayName());
    }

    @Override
    public InteractionResult use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        Spell spell = getSpell(stack);
        if (spell == null) {
            return InteractionResult.FAIL;
        }
        if (level.isClientSide()) {
            return InteractionResult.SUCCESS;
        }
        if (!SpellCasting.learn(player, spell)) {
            player.sendOverlayMessage(Component.translatable("message.spellmod.already_known", spell.displayName()).withStyle(ChatFormatting.GRAY));
            return InteractionResult.FAIL;
        }
        stack.consume(1, player);
        level.playSound(null, player.getX(), player.getY(), player.getZ(), SoundEvents.ENCHANTMENT_TABLE_USE, SoundSource.PLAYERS, 1.0F, 1.0F);
        player.sendSystemMessage(Component.translatable("message.spellmod.learned",
                spell.displayName().withStyle(ChatFormatting.AQUA), spell.minStage().displayName(), spell.baseManaCost()));
        return InteractionResult.SUCCESS_SERVER;
    }
}
