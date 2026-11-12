package dev.lumina.client;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.math.Axis;
import dev.lumina.blockentity.PedestalBlockEntity;
import net.minecraft.client.renderer.LightTexture;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.blockentity.BlockEntityRenderer;
import net.minecraft.client.renderer.blockentity.BlockEntityRendererProvider;
import net.minecraft.client.renderer.entity.ItemRenderer;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;

/** Draws the pedestal's item slowly spinning above its top plate. */
public class PedestalRenderer implements BlockEntityRenderer<PedestalBlockEntity> {
    private final ItemRenderer itemRenderer;

    public PedestalRenderer(BlockEntityRendererProvider.Context context) {
        this.itemRenderer = context.getItemRenderer();
    }

    @Override
    public void render(PedestalBlockEntity pedestal, float partialTick, PoseStack pose, MultiBufferSource buffers,
            int light, int overlay) {
        ItemStack stack = pedestal.getItem();
        if (stack.isEmpty() || pedestal.getLevel() == null) {
            return;
        }
        float time = pedestal.getLevel().getGameTime() + partialTick;
        pose.pushPose();
        pose.translate(0.5, 1.2 + Math.sin(time / 10.0) * 0.04, 0.5);
        pose.mulPose(Axis.YP.rotationDegrees(time * 2.0F % 360.0F));
        pose.scale(0.5F, 0.5F, 0.5F);
        itemRenderer.renderStatic(stack, ItemDisplayContext.FIXED, LightTexture.FULL_BRIGHT,
                OverlayTexture.NO_OVERLAY, pose, buffers, pedestal.getLevel(), 0);
        pose.popPose();
    }
}
