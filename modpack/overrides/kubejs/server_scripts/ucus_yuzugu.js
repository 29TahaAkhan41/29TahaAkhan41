// Göksel Uçuş Yüzüğü: envanterde taşındığı sürece yaratıcı moddaki gibi uçuş verir.

PlayerEvents.tick(event => {
  const player = event.player
  if (player.age % 20 !== 0) return
  if (player.isCreative() || player.isSpectator()) return

  const hasRing = player.inventory.countItem(Item.of('kubejs:flight_ring').item) > 0
  const data = player.persistentData
  const abilities = player.abilities

  if (hasRing && !abilities.mayfly) {
    abilities.mayfly = true
    data.putBoolean('yy_ring_flight', true)
    player.onUpdateAbilities()
  } else if (!hasRing && data.getBoolean('yy_ring_flight')) {
    abilities.mayfly = false
    abilities.flying = false
    data.putBoolean('yy_ring_flight', false)
    player.onUpdateAbilities()
  }
})
