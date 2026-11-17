// İlk girişte görev kitabını ver.

PlayerEvents.loggedIn(event => {
  const player = event.player
  if (player.stages.has('yy_starter_book')) return
  player.stages.add('yy_starter_book')
  player.give('ftbquests:book')
  player.tell(Text.translatable('message.kubejs.welcome').gold())
})
