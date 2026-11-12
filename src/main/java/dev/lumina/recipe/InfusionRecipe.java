package dev.lumina.recipe;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import dev.lumina.Lumina;
import net.minecraft.core.HolderLookup;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.util.ExtraCodecs;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.SingleRecipeInput;
import net.minecraft.world.level.Level;

/** Turns one item into another on an infusion pedestal, at the cost of some starlight. */
public record InfusionRecipe(Ingredient ingredient, ItemStack result, int starlight)
        implements Recipe<SingleRecipeInput> {

    @Override
    public boolean matches(SingleRecipeInput input, Level level) {
        return ingredient.test(input.item());
    }

    @Override
    public ItemStack assemble(SingleRecipeInput input, HolderLookup.Provider registries) {
        return result.copy();
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return true;
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registries) {
        return result;
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return Lumina.INFUSION_SERIALIZER.get();
    }

    @Override
    public RecipeType<?> getType() {
        return Lumina.INFUSION_TYPE.get();
    }

    public static class Serializer implements RecipeSerializer<InfusionRecipe> {
        private static final MapCodec<InfusionRecipe> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
                Ingredient.CODEC_NONEMPTY.fieldOf("ingredient").forGetter(InfusionRecipe::ingredient),
                ItemStack.STRICT_CODEC.fieldOf("result").forGetter(InfusionRecipe::result),
                ExtraCodecs.POSITIVE_INT.fieldOf("starlight").forGetter(InfusionRecipe::starlight)
        ).apply(instance, InfusionRecipe::new));

        private static final StreamCodec<RegistryFriendlyByteBuf, InfusionRecipe> STREAM_CODEC = StreamCodec.composite(
                Ingredient.CONTENTS_STREAM_CODEC, InfusionRecipe::ingredient,
                ItemStack.STREAM_CODEC, InfusionRecipe::result,
                ByteBufCodecs.VAR_INT, InfusionRecipe::starlight,
                InfusionRecipe::new);

        @Override
        public MapCodec<InfusionRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, InfusionRecipe> streamCodec() {
            return STREAM_CODEC;
        }
    }
}
