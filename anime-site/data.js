// Katalog verisi. Yeni anime eklemek için bu listeye bir nesne ekleyin.
// video: mp4/webm adresi (yalnızca yayın hakkına sahip olduğunuz içerik!)
// subs:  Türkçe WebVTT altyazı dosyası (subs/ klasörü)
window.CATALOG = [
  {
    id: "sintel",
    title: "Sintel",
    jp: "シンテル",
    year: 2010,
    genres: ["Fantastik", "Macera", "Dram"],
    rating: 8.4,
    colors: ["#5b2a86", "#e0607e"],
    synopsis:
      "Genç bir kız olan Sintel, yaralı bulup büyüttüğü yavru ejderhası Scales'i kaçıran dev bir ejderhanın peşine düşer. Karlı dağlardan çöl şehirlerine uzanan bu yolculukta bedeli ağır bir gerçekle yüzleşecektir.",
    credit: "© Blender Foundation · durian.blender.org · CC BY 3.0",
    episodes: [
      {
        n: 1,
        title: "Ejderha Avcısı",
        duration: "14:48",
        video: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
        subs: "subs/sintel-tr.vtt"
      }
    ]
  },
  {
    id: "tears-of-steel",
    title: "Tears of Steel",
    jp: "鋼の涙",
    year: 2012,
    genres: ["Bilim Kurgu", "Aksiyon"],
    rating: 7.6,
    colors: ["#0f3d5e", "#38bdf8"],
    synopsis:
      "Gelecekteki Amsterdam'da bir grup savaşçı ve bilim insanı, dünyayı robotların istilasından kurtarmak için geçmişteki tek bir anı yeniden canlandırmaya çalışır.",
    credit: "© Blender Foundation · mango.blender.org · CC BY 3.0",
    episodes: [
      {
        n: 1,
        title: "Amsterdam'daki Köprü",
        duration: "12:14",
        video: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        subs: "subs/tears-of-steel-tr.vtt"
      }
    ]
  },
  {
    id: "elephants-dream",
    title: "Elephants Dream",
    jp: "象の夢",
    year: 2006,
    genres: ["Gerilim", "Gizem", "Bilim Kurgu"],
    rating: 6.9,
    colors: ["#3f3a1f", "#d9a441"],
    synopsis:
      "Emo ve Proog, sonsuz bir makinenin içinde dolaşır. Proog bu dünyayı tanıdığını iddia eder; Emo ise gördüklerine inanmaz. Gerçeklik ile hayal arasındaki çizgi giderek bulanıklaşır.",
    credit: "© Blender Foundation · orange.blender.org · CC BY 2.5",
    episodes: [
      {
        n: 1,
        title: "Makinenin İçinde",
        duration: "10:53",
        video: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        subs: "subs/elephants-dream-tr.vtt"
      }
    ]
  },
  {
    id: "big-buck-bunny",
    title: "Big Buck Bunny",
    jp: "ビッグ・バック・バニー",
    year: 2008,
    genres: ["Komedi", "Macera"],
    rating: 7.3,
    colors: ["#1f5130", "#9ad14b"],
    synopsis:
      "İri ve iyi kalpli bir tavşan, ormandaki üç yaramaz kemirgenin zorbalığına uğrar. Sabrı taşınca intikam için kendine özgü, yaratıcı bir plan kurar.",
    credit: "© Blender Foundation · peach.blender.org · CC BY 3.0",
    episodes: [
      {
        n: 1,
        title: "Ormanın Kralı",
        duration: "9:56",
        video: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        subs: "subs/big-buck-bunny-tr.vtt"
      }
    ]
  }
];
