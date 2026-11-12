package dev.lumina.item;

import dev.lumina.Lumina;
import dev.lumina.blockentity.StarlightNodeBlockEntity;
import dev.lumina.starlight.LinkResult;
import dev.lumina.starlight.StarlightSky;
import java.util.List;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;

/**
 * Aims beams. Click the emitting node, then the receiving node. Sneak-click a node to drop all of
 * its beams. Used in the open air it reads out the current starlight intensity.
 */
public class LinkingWandItem extends Item {
    public LinkingWandItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResult useOn(UseOnContext context) {
        Level level = context.getLevel();
        BlockPos pos = context.getClickedPos();
        Player player = context.getPlayer();
        ItemStack wand = context.getItemInHand();
        if (!(level.getBlockEntity(pos) instanceof StarlightNodeBlockEntity node)) {
            return InteractionResult.PASS;
        }
        if (level.isClientSide || player == null) {
            return InteractionResult.SUCCESS;
        }

        if (player.isSecondaryUseActive()) {
            int removed = node.clearLinks();
            wand.remove(Lumina.LINK_SOURCE);
            say(player, Component.translatable("message.lumina.link.cleared", removed), ChatFormatting.YELLOW);
            return InteractionResult.CONSUME;
        }

        BlockPos source = wand.get(Lumina.LINK_SOURCE);
        if (source == null) {
            if (node.getMaxTargets() <= 0) {
                say(player, Component.translatable(LinkResult.CANNOT_EMIT.translationKey()), ChatFormatting.RED);
            } else {
                wand.set(Lumina.LINK_SOURCE, pos.immutable());
                say(player, Component.translatable("message.lumina.link.source_set"), ChatFormatting.AQUA);
            }
            return InteractionResult.CONSUME;
        }

        wand.remove(Lumina.LINK_SOURCE);
        LinkResult result = level.isLoaded(source)
                && level.getBlockEntity(source) instanceof StarlightNodeBlockEntity sourceNode
                        ? sourceNode.link(pos)
                        : LinkResult.NOT_A_NODE;
        boolean linked = result == LinkResult.LINKED;
        say(player, Component.translatable(result.translationKey()), linked ? ChatFormatting.GREEN : ChatFormatting.RED);
        if (linked) {
            level.playSound(null, pos, SoundEvents.AMETHYST_BLOCK_RESONATE, SoundSource.BLOCKS, 1.0F, 1.0F);
        }
        return InteractionResult.CONSUME;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack wand = player.getItemInHand(hand);
        if (!level.isClientSide) {
            if (player.isSecondaryUseActive() && wand.has(Lumina.LINK_SOURCE)) {
                wand.remove(Lumina.LINK_SOURCE);
                say(player, Component.translatable("message.lumina.link.cancelled"), ChatFormatting.YELLOW);
            } else {
                int percent = Math.round(StarlightSky.intensity(level, player.blockPosition()) * 100.0F);
                say(player, Component.translatable("message.lumina.sky", percent), ChatFormatting.AQUA);
            }
        }
        return InteractionResultHolder.sidedSuccess(wand, level.isClientSide);
    }

    @Override
    public boolean isFoil(ItemStack stack) {
        return stack.has(Lumina.LINK_SOURCE);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        BlockPos source = stack.get(Lumina.LINK_SOURCE);
        if (source != null) {
            tooltip.add(Component.translatable("tooltip.lumina.linking_wand.source",
                    source.getX(), source.getY(), source.getZ()).withStyle(ChatFormatting.AQUA));
        }
        tooltip.add(Component.translatable("tooltip.lumina.linking_wand.hint").withStyle(ChatFormatting.GRAY));
    }

    private static void say(Player player, Component message, ChatFormatting color) {
        player.displayClientMessage(message.copy().withStyle(color), true);
    }
}
