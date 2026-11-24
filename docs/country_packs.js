/* country_packs.js — extra, researched slides for selected countries (English + Arabic).
 * A pack adds: context (what drives need · development opportunities) after the executive summary; a governorate
 * atlas (two maps per slide) after the sector slides; a sector-by-sector view for each focus area (focus_areas.js);
 * optional extra figures (`data`) and per-sector stat cards (`sectorStats`); and, if given, a `recommendations` slide before
 * the method slide. Content is dated (asOf) — review it when sources update.
 * Map values are keyed by the region names in data/subnational/{ISO3}.json (the outlines come from there).
 * Every text is [English, Arabic].
 */
'use strict';
const COUNTRY_PACKS = {
  Jordan: {
    asOf: '2026-11',
    // ── refugee situation (slide after the executive summary) ──
    refugees: {
      tagline: ['a large host country, now seeing returns to Syria', 'بلد مضيف كبير يشهد الآن عودة اللاجئين إلى سوريا'],
      map: 'refugees',
      facts: [
        ['341,598', ['Refugees and asylum-seekers registered with UNHCR', 'اللاجئون وطالبو اللجوء المسجلون لدى المفوضية'], ['31 Oct 2026 · 93% Syrian, plus Iraqi, Yemeni and Sudanese · excludes Palestine refugees', '31 أكتوبر 2026 · 93% سوريون، إضافة إلى عراقيين ويمنيين وسودانيين · لا يشمل لاجئي فلسطين']],
        ['318,813', ['Registered Syrian refugees', 'اللاجئون السوريون المسجلون'], ['Down from 611,473 in Dec 2024 · 23% in camps', 'انخفاضاً من 611,473 في ديسمبر 2024 · 23% في المخيمات']],
        [['~220,000', '~220,000'], ['Syrians returned since Dec 2024', 'السوريون العائدون منذ ديسمبر 2024'], ['UNHCR, to late Aug 2026', 'المفوضية، حتى أواخر أغسطس 2026']],
        [['2.4 million', '2.4 مليون'], ['Palestine refugees registered with UNRWA', 'لاجئو فلسطين المسجلون لدى الأونروا'], ['A separate group: displaced in 1948 and 1967, and their descendants · most are Jordanian citizens', 'فئة منفصلة: هُجّروا في 1948 و1967 وذريتهم · ومعظمهم مواطنون أردنيون']],
        ['28%', ["UNHCR's 2026 appeal funded", 'نسبة تمويل نداء المفوضية لعام 2026'], ['US$280 million required · mid-2026', '280 مليون دولار مطلوبة · منتصف 2026']],
      ],
      points: [
        [['Where they live', 'أماكن الإقامة'], ['77% live in towns and cities rather than camps; Amman, Mafraq, Irbid and Zarqa host 89%. Zaatari (Mafraq) and Azraq (Zarqa) are the main camps.',
          'يعيش 77% في المدن والبلدات لا في المخيمات، وتستضيف عمّان والمفرق وإربد والزرقاء 89% منهم. والزعتري (المفرق) والأزرق (الزرقاء) أكبر المخيمات.']],
        [['Returns', 'العودة'], ['Since December 2024 registered Syrians have almost halved as families return; UNHCR extended its return cash assistance to refugees outside camps in September 2026.',
          'منذ ديسمبر 2024 انخفض عدد السوريين المسجلين إلى النصف تقريباً مع عودة الأسر، وتدعم المفوضية العودة الطوعية ووسّعت في سبتمبر 2026 مساعدتها النقدية للعودة لتشمل اللاجئين خارج المخيمات.']],
        [['Pressure on services', 'الضغط على الخدمات'], ['Refugees use the same schools, clinics and water networks as Jordanians, mostly in the north and centre, where water shortages and anaemia are also highest.',
          'يستخدم اللاجئون المدارس والعيادات وشبكات المياه نفسها التي يستخدمها الأردنيون، ولا سيما في الشمال والوسط حيث يرتفع أيضاً نقص المياه وفقر الدم.']],
        [['Funding', 'التمويل'], ["UNHCR's 2026 appeal was 28% funded by mid-year; health, cash and child-protection services were already scaled back in 2025.",
          'لم يُموَّل نداء المفوضية لعام 2026 إلا بنسبة 28% حتى منتصف العام، وكانت خدمات الصحة والمساعدات النقدية وحماية الطفل قد قُلّصت في 2025.']],
      ],
      support: [
        ['Strengthen shared services — schools, clinics and water — in Amman, Mafraq, Irbid and Zarqa, so host communities and refugees both benefit.',
         'تعزيز الخدمات المشتركة، من مدارس وعيادات ومياه، في عمّان والمفرق وإربد والزرقاء ليستفيد منها المجتمع المضيف واللاجئون معاً.'],
        ['Help refugees who stay become self-reliant through work permits, skills and small-business support.',
         'مساعدة اللاجئين الباقين على الاعتماد على أنفسهم عبر تصاريح العمل والمهارات ودعم المشروعات الصغيرة.'],
        ['Support safe, voluntary and lasting returns, and plan for camps that are shrinking.',
         'دعم العودة الآمنة والطوعية والمستدامة، والتخطيط لتقلّص المخيمات.'],
      ],
      sources: ['UNHCR (data portal, 31 Oct 2026; funding update, mid-2026; returns update, Aug 2026) · UNRWA',
                'المفوضية (بوابة البيانات، 31 أكتوبر 2026؛ تحديث التمويل منتصف 2026؛ تحديث العودة أغسطس 2026) · الأونروا'],
    },
    // ── context: what drives need ──
    drivers: {
      facts: [
        ['21.4%', ['Unemployment among Jordanians', 'البطالة بين الأردنيين'], ['Q3 2025 · women 33.9%, men 18.0%', 'الربع الثالث 2025 · النساء 33.9% والرجال 18.0%']],
        ['14.4%', ["Women's labour-force participation", 'مشاركة المرأة في القوى العاملة'], ['Q3 2025 · Arab average 18.1%', 'الربع الثالث 2025 · المتوسط العربي 18.1%']],
        ['61 m³', ['Renewable water per person a year', 'المياه المتجددة للفرد سنوياً'], ['Absolute scarcity line: 500 m³', 'خط الشح المطلق: 500 م³']],
        ['318,813', ['Registered Syrian refugees', 'اللاجئون السوريون المسجلون'], ['UNHCR, 31 Oct 2026 · down from 611,473 in Dec 2024', 'المفوضية، 31 أكتوبر 2026 · انخفاضاً من 611,473 في ديسمبر 2024']],
        ['108%', ['Public debt, % of GDP (2026)', 'الدين العام (% من الناتج، 2026)'], ['IMF · 82% net of Social Security holdings', 'صندوق النقد · 82% بعد استبعاد حيازات الضمان الاجتماعي']],
      ],
      points: [
        [['Jobs', 'فرص العمل'], ['One in five Jordanians in the labour force is unemployed, and one in three women; only one woman in seven is in the labour force. Unemployment is highest in Ma\'an (29.4%), Jerash (27.3%), Balqa (26.4%) and Irbid (24.9%).',
          'عاطل واحد من كل خمسة أردنيين في القوى العاملة، وواحدة من كل ثلاث نساء؛ ولا تشارك في سوق العمل سوى امرأة واحدة من كل سبع. وتبلغ البطالة أعلى مستوياتها في معان (29.4%) وجرش (27.3%) والبلقاء (26.4%) وإربد (24.9%).']],
        [['Water', 'المياه'], ['Jordan is among the most water-scarce countries in the world, and close to half of piped water is lost to leaks, theft and metering errors. The National Water Carrier — a plant at Aqaba that will desalinate Red Sea water and pump it more than 400 km north to Amman and other governorates — is due in 2030.',
          'الأردن من أشد دول العالم شحاً في المياه، ويُفقد نحو نصف المياه المنقولة بالشبكات بسبب التسرب والسرقة وأخطاء القياس. ويُنتظر في 2030 تشغيل ناقل المياه الوطني، وهو محطة في العقبة لتحلية مياه البحر الأحمر وضخّها أكثر من 400 كم شمالاً إلى عمّان والمحافظات الأخرى.']],
        [['Refugee hosting', 'استضافة اللاجئين'], ['Jordan hosts 318,813 registered Syrian refugees — 77% in towns and cities, mostly Amman, Mafraq, Irbid and Zarqa — alongside about 2.4 million registered Palestine refugees, which stretches schools, clinics and water (see the refugee slide).',
          'يستضيف الأردن 318,813 لاجئاً سورياً مسجلاً، 77% منهم في المدن والبلدات، ولا سيما عمّان والمفرق وإربد والزرقاء، إلى جانب نحو 2.4 مليون لاجئ فلسطيني مسجل، ما يضغط على المدارس والعيادات والمياه (انظر شريحة اللاجئين).']],
        [['Fiscal space', 'الحيّز المالي'], ['High public debt and an IMF Extended Fund Facility (reviews completed through mid-2026) limit public investment; growth is forecast at 2.7% in 2026 and 3.1% in 2027.',
          'يحدّ ارتفاع الدين العام وبرنامج «تسهيل الصندوق الممدد» مع صندوق النقد الدولي (استُكملت مراجعاته حتى منتصف 2026) من الاستثمار العام؛ ويُتوقع نمو بنسبة 2.7% في 2026 و3.1% في 2027.']],
      ],
      sources: ['Jordan DoS (Labour Force Survey Q3 2025) · UNHCR (Apr 2026) · IMF · Ministry of Water · UNRWA',
                'دائرة الإحصاءات العامة (مسح القوى العاملة، الربع الثالث 2025) · المفوضية السامية لشؤون اللاجئين · صندوق النقد الدولي · وزارة المياه · الأونروا'],
    },
    // ── context: development opportunities ──
    opportunities: {
      vision: [['Economic Modernisation Vision 2033', 'رؤية التحديث الاقتصادي 2033'],
        ['Targets about 5.6% real growth a year, more than one million jobs over the decade and around US$4 billion of foreign investment a year. The 2026–2029 executive programme (launched January 2026) has about 393 projects, many with the private sector.',
         'تستهدف نمواً حقيقياً بنحو 5.6% سنوياً، وأكثر من مليون فرصة عمل خلال العقد، ونحو 4 مليارات دولار من الاستثمار الأجنبي سنوياً. ويضم البرنامج التنفيذي 2026–2029 (أُطلق في يناير 2026) نحو 393 مشروعاً، كثير منها بالشراكة مع القطاع الخاص.']],
      projects: [
        [['Water — National Water Carrier', 'المياه — ناقل المياه الوطني'], ['300 million m³ a year desalinated at Aqaba (about 40% of drinking water), about US$6 billion, ground broken Nov 2026, operating 2030.',
          '300 مليون م³ سنوياً تُحلّى في العقبة (نحو 40% من مياه الشرب)، بقيمة تقارب 6 مليارات دولار، وُضع حجر أساسه في نوفمبر 2026 ويبدأ تشغيله في 2030.']],
        [['Transport — Aqaba railway', 'النقل — سكة حديد العقبة'], ['US$2.3 billion UAE–Jordan joint venture, 360 km from the port to the phosphate and potash mines (signed Apr 2026).',
          'مشروع مشترك إماراتي–أردني بقيمة 2.3 مليار دولار، بطول 360 كم من الميناء إلى مناجم الفوسفات والبوتاس (وُقّع في أبريل 2026).']],
        [['Energy — green hydrogen and ammonia', 'الطاقة — الهيدروجين والأمونيا الخضراء'], ['First US$1 billion green ammonia plant at Aqaba (May 2026; up to 550 MW of solar); 14 hydrogen and ammonia projects planned for 2026–2029, with EBRD support for an Aqaba hub.',
          'أول مصنع للأمونيا الخضراء في العقبة بقيمة مليار دولار (مايو 2026؛ حتى 550 ميغاواط من الطاقة الشمسية)؛ و14 مشروعاً للهيدروجين والأمونيا مخطط لها في 2026–2029، بدعم من البنك الأوروبي لإعادة الإعمار والتنمية لإنشاء مركز في العقبة.']],
        [['Ports and logistics', 'الموانئ والخدمات اللوجستية'], ['Record container volumes in 2025 (1.0 million TEU) and a 30-year AD Ports Group concession for the multipurpose port (Feb 2026); rising transit trade to Syria and Iraq.',
          'أحجام حاويات قياسية في 2025 (مليون حاوية نمطية)، وامتياز لمجموعة موانئ أبوظبي لمدة 30 عاماً للميناء متعدد الأغراض (فبراير 2026)؛ مع تنامي تجارة الترانزيت إلى سوريا والعراق.']],
        [['Digital economy', 'الاقتصاد الرقمي'], ['EU-backed Aqaba Digital Hub and Medusa cable extension (Nov 2026); national push on data centres, cloud and AI.',
          'مركز العقبة الرقمي وتمديد كابل «ميدوسا» بدعم أوروبي (نوفمبر 2026)؛ وتوجه وطني نحو مراكز البيانات والحوسبة السحابية والذكاء الاصطناعي.']],
      ],
      partners: [
        [['UAE', 'الإمارات'], ['US$5.5 billion investment framework (2023), the Aqaba railway, AD Ports\' concession and Emirati partners in green ammonia.',
          'إطار استثماري بقيمة 5.5 مليار دولار (2023)، وسكة حديد العقبة، وامتياز موانئ أبوظبي، وشركاء إماراتيون في الأمونيا الخضراء.']],
        [['European Union', 'الاتحاد الأوروبي'], ['€3 billion package for 2025–2027 and the first Jordan–EU Investment Conference (Nov 2026).',
          'حزمة بقيمة 3 مليارات يورو للفترة 2025–2027، وأول مؤتمر استثمار أردني–أوروبي (نوفمبر 2026).']],
        [['Saudi Arabia', 'السعودية'], ['Jordan\'s largest investor in 2025 (16% of FDI); economic-zones MoU in April 2026.',
          'أكبر مستثمر في الأردن عام 2025 (16% من الاستثمار الأجنبي المباشر)؛ ومذكرة تفاهم للمناطق الاقتصادية في أبريل 2026.']],
      ],
      sources: ['Ministry of Planning (EMV executive programme 2026–2029) · Petra · AD Ports Group · EU · EBRD · IMF',
                'وزارة التخطيط (البرنامج التنفيذي 2026–2029) · بترا · موانئ أبوظبي · الاتحاد الأوروبي · البنك الأوروبي لإعادة الإعمار والتنمية · صندوق النقد الدولي'],
    },
    // ── governorate atlas: two maps per slide ──
    atlas: [
      { after: 'wash', title: ['Drinking water', 'مياه الشرب'],
        statement: ['shortages are worst in Jerash and Mafraq, and nearly half of households rely on bottled water', 'النقص أشدّ في جرش والمفرق، ونحو نصف الأسر تعتمد على المياه المعبأة'],
        maps: ['shortage', 'bottled'] },
      { after: 'health', title: ['Child health', 'صحة الطفل'],
        statement: ["vaccination gaps in Ma'an, Madaba and Aqaba; stunting highest in Mafraq and Ma'an", 'فجوات التحصين في معان ومادبا والعقبة، والتقزّم أعلى في المفرق ومعان'],
        maps: ['vacc', 'stunt'] },
      { after: 'econ', title: ['Jobs', 'فرص العمل'],
        statement: ["unemployment is highest in Ma'an, Jerash, Balqa and Irbid", 'البطالة أعلى في معان وجرش والبلقاء وإربد'],
        maps: ['unemp'],
        points: [
          [['Women', 'النساء'], ['One in three women in the labour force is unemployed (33.9%), against 18.0% of men, and only one woman in seven is in the labour force (Q3 2025).',
            'امرأة واحدة من كل ثلاث نساء في القوى العاملة عاطلة عن العمل (33.9%) مقابل 18.0% من الرجال، ولا تشارك في سوق العمل سوى امرأة واحدة من كل سبع (الربع الثالث 2025).']],
          [['Young people', 'الشباب'], ['About two in five young people in the labour force are unemployed (38.9%, ILO 2025), and people aged 15–24 are 18.7% of the population.',
            'نحو اثنين من كل خمسة شباب في القوى العاملة عاطلون عن العمل (38.9%، منظمة العمل الدولية 2025)، ويشكّل من هم بعمر 15–24 نسبة 18.7% من السكان.']],
          [['Where', 'أين'], ["Ma'an (29.4%), Jerash (27.3%), Balqa (26.4%) and Irbid (24.9%) are above the national 21.4%. Jerash also has the most water shortages and the highest anaemia among women.",
            'تتجاوز معان (29.4%) وجرش (27.3%) والبلقاء (26.4%) وإربد (24.9%) المعدل الوطني البالغ 21.4%، وتسجّل جرش أيضاً أعلى نقص في المياه وأعلى نسبة فقر دم بين النساء.']],
          [['What it means', 'ماذا يعني ذلك'], ['Job programmes should target these governorates, women and young people, linking training, childcare and transport to employers in the national projects.',
            'ينبغي أن تستهدف برامج التشغيل هذه المحافظات والنساء والشباب، وأن تربط التدريب ورعاية الأطفال والنقل بأصحاب العمل في المشاريع الوطنية.']],
        ] },
    ],
    maps: {
      unemp: { name: ['Unemployment among Jordanians', 'البطالة بين الأردنيين'], unit: '%', worse: 'high', national: 21.4,
        source: ['DoS Labour Force Survey, Q3 2025', 'مسح القوى العاملة، الربع الثالث 2025'],
        values: { Amman: 19.5, Balqa: 26.4, Zarqa: 18.2, Madaba: 21.4, Irbid: 24.9, Mafraq: 24.3, Jarash: 27.3, Ajloun: 20.6, Karak: 17.3, Tafiela: 19.0, "Ma'an": 29.4, Aqaba: 18.9 },
        reading: ["Highest in Ma'an (29.4%, eight points above the national rate) and Jerash (27.3%); lowest in Karak (17.3%).",
                  'الأعلى في معان (29.4%، أي ثماني نقاط فوق المعدل الوطني) وجرش (27.3%)؛ والأدنى في الكرك (17.3%).'] },
      refugees: { name: ['Registered Syrian refugees by governorate', 'اللاجئون السوريون المسجلون حسب المحافظة'], unit: 'count', worse: 'high', national: null,
        source: ['UNHCR, 31 Oct 2026 · camps counted in their governorate', 'المفوضية، 31 أكتوبر 2026 · المخيمات ضمن محافظاتها'],
        values: { Amman: 99123, Mafraq: 85638, Irbid: 51898, Zarqa: 48536, Balqa: 8730, Madaba: 6933, "Ma'an": 5177, Karak: 3917, Jarash: 3483, Aqaba: 2365, Ajloun: 2140, Tafiela: 758 },
        reading: ['Amman, Mafraq (including Zaatari camp), Irbid and Zarqa (including Azraq camp) host 89% of registered Syrian refugees.',
                  'تستضيف عمّان والمفرق (بما فيها مخيم الزعتري) وإربد والزرقاء (بما فيها مخيم الأزرق) 89% من اللاجئين السوريين المسجلين.'] },
      shortage: { name: ['Water stress: people without enough drinking water in the past month', 'الإجهاد المائي: السكان دون مياه شرب كافية خلال الشهر الماضي'], unit: '%', worse: 'high', national: 15.1,
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        values: { Amman: 9.1, Balqa: 20.9, Zarqa: 13.7, Madaba: 28.9, Irbid: 11.7, Mafraq: 39.9, Jarash: 41.9, Ajloun: 24.0, Karak: 22.0, Tafiela: 7.8, "Ma'an": 21.8, Aqaba: 25.6 },
        reading: ['About two in five people in Jerash (41.9%) and Mafraq (39.9%) did not have enough drinking water in the past month, against 15.1% nationally; Madaba (28.9%) and Aqaba (25.6%) follow.',
                  'لم يحصل نحو اثنين من كل خمسة أشخاص في جرش (41.9%) والمفرق (39.9%) على مياه شرب كافية خلال الشهر الماضي، مقابل 15.1% على المستوى الوطني، وتليهما مادبا (28.9%) والعقبة (25.6%).'] },
      piped: { name: ['Households drinking piped water at home', 'الأسر التي تشرب مياه الشبكة في المنزل'], unit: '%', worse: 'low', national: 49.0,
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        values: { Amman: 47.0, Balqa: 58.6, Zarqa: 55.4, Madaba: 34.7, Irbid: 33.0, Mafraq: 89.3, Jarash: 29.3, Ajloun: 40.4, Karak: 55.0, Tafiela: 43.1, "Ma'an": 70.1, Aqaba: 88.6 },
        reading: ['Only 29% of households in Jerash, 33% in Irbid and 35% in Madaba drink water piped into the home, against 49% nationally; supply is intermittent in much of Jordan, so many households buy water instead.',
                  'لا تشرب مياه الشبكة في المنزل سوى 29% من الأسر في جرش و33% في إربد و35% في مادبا، مقابل 49% على المستوى الوطني؛ إذ تصل الإمدادات بشكل متقطع في معظم أنحاء الأردن، فتشتري أسر كثيرة المياه بدلاً منها.'] },
      bottled: { name: ['Households relying on bottled water', 'الأسر التي تعتمد على المياه المعبأة'], unit: '%', worse: 'high', national: 46.6,
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        values: { Amman: 52.1, Balqa: 36.5, Zarqa: 43.7, Madaba: 61.7, Irbid: 53.0, Mafraq: 3.6, Jarash: 64.4, Ajloun: 42.8, Karak: 43.7, Tafiela: 56.7, "Ma'an": 28.7, Aqaba: 10.0 },
        reading: ['Bottled water is the main drinking source for 64% of households in Jerash, 62% in Madaba and 57% in Tafiela (national 46.6%) — a recurring cost for families that the National Water Carrier and network repairs aim to reduce.',
                  'المياه المعبأة هي المصدر الرئيسي للشرب لدى 64% من الأسر في جرش و62% في مادبا و57% في الطفيلة (الوطني 46.6%)، وهي كلفة متكررة على الأسر يسعى ناقل المياه الوطني وإصلاح الشبكات إلى خفضها.'] },
      vacc: { dhs: 'health', name: ['Children with all basic vaccinations', 'الأطفال الحاصلون على جميع التطعيمات الأساسية'], unit: '%', worse: 'low',
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        reading: ["Ma'an (69.6%) and Madaba (80.8%) lag far behind the national 91.7%; Aqaba (84.1%) is third-lowest.",
                  'تتأخر معان (69.6%) ومادبا (80.8%) كثيراً عن المعدل الوطني البالغ 91.7%، وتأتي العقبة (84.1%) في المرتبة الثالثة من الأدنى.'] },
      stunt: { dhs: 'food', name: ['Child stunting (under 5)', 'تقزّم الأطفال دون الخامسة'], unit: '%', worse: 'high',
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        reading: ["Mafraq (15.2%), Ma'an (13.0%) and Tafiela (12.7%) are above 10%, the WHO threshold for a medium public-health concern; the national rate is 8.3%.",
                  'تتجاوز المفرق (15.2%) ومعان (13.0%) والطفيلة (12.7%) نسبة 10%، وهي عتبة منظمة الصحة العالمية لمشكلة صحة عامة متوسطة، فيما يبلغ المعدل الوطني 8.3%.'] },
    },
    // ── focus area sector by sector (by focus key) ──
    focusSectors: {
      aqaba: [
        // [sector EN/AR, rating 'strength'|'mixed'|'gap', text EN/AR]
        [['Water', 'المياه'], 'mixed', ['Good access — every household uses an improved source and 89% have piped water at home — but one in four people (25.6%) lacked enough drinking water in the past month (national 15.1%, DHS 2023). Relief comes with the National Water Carrier (50 million m³ a year for Aqaba) from 2030.',
          'وصول جيد، إذ تستخدم جميع الأسر مصدراً محسّناً و89% منها لديها مياه الشبكة في المنزل، لكن ربع السكان (25.6%) لم يحصلوا على مياه شرب كافية خلال الشهر الماضي (الوطني 15.1%، 2023). ويأتي الحل مع ناقل المياه الوطني (50 مليون م³ سنوياً للعقبة) اعتباراً من 2030.']],
        [['Energy', 'الطاقة'], 'strength', ['Jordan\'s green hydrogen hub: US$1 billion green ammonia plant (May 2026, up to 550 MW of solar) and EBRD technical support; the plant and port will need reliable clean power.',
          'مركز الأردن للهيدروجين الأخضر: مصنع أمونيا خضراء بقيمة مليار دولار (مايو 2026، حتى 550 ميغاواط شمسية) ودعم فني من البنك الأوروبي؛ ويحتاج المصنع والميناء إلى طاقة نظيفة موثوقة.']],
        [['Agriculture & food security', 'الزراعة والأمن الغذائي'], 'mixed', ['Little farmland — food arrives through the port; child stunting (8.8%) and child anaemia (33.1%) are slightly above the national rates (8.3%, 32.0%).',
          'رقعة زراعية محدودة ويصل الغذاء عبر الميناء؛ ونسبتا تقزّم الأطفال (8.8%) وفقر الدم لديهم (33.1%) أعلى قليلاً من المعدلين الوطنيين (8.3% و32.0%).']],
        [['Education', 'التعليم'], 'mixed', ['Women\'s literacy 95.5% (national 96.7%); the main gap is technical skills for ports, rail, logistics and digital jobs.',
          'معرفة النساء بالقراءة والكتابة 95.5% (الوطني 96.7%)؛ والفجوة الأهم هي المهارات التقنية لوظائف الموانئ والسكك الحديدية والخدمات اللوجستية والرقمية.']],
        [['Health', 'الصحة'], 'gap', ['Child vaccination 84.1% against 91.7% nationally (third-lowest governorate); women\'s anaemia 35.8% against 32.3%.',
          'تحصين الأطفال 84.1% مقابل 91.7% وطنياً (ثالث أدنى محافظة)؛ وفقر الدم لدى النساء 35.8% مقابل 32.3%.']],
        [['Economic empowerment', 'التمكين الاقتصادي'], 'mixed', ['Unemployment among Jordanians 18.9% (Q3 2025), below the national 21.4%; about 61,000 jobs in the special economic zone, but few women in work.',
          'البطالة بين الأردنيين 18.9% (الربع الثالث 2025)، أدنى من المعدل الوطني البالغ 21.4%؛ ونحو 61,000 وظيفة في المنطقة الاقتصادية الخاصة، مع مشاركة محدودة للنساء.']],
        [['Business enablement', 'تمكين بيئة الأعمال'], 'strength', ['Special economic zone since 2001 with tax and customs incentives, new investment waivers in 2026 and the EU-backed Aqaba Digital Hub.',
          'منطقة اقتصادية خاصة منذ 2001 بحوافز ضريبية وجمركية، وإعفاءات استثمارية جديدة في 2026، ومركز العقبة الرقمي بدعم أوروبي.']],
        [['Trade', 'التجارة'], 'strength', ['Jordan\'s only seaport: 1.0 million TEU in 2025 (+22%), transit to Syria up 168%, and the Aqaba railway to the mines.',
          'الميناء البحري الوحيد في الأردن: مليون حاوية نمطية في 2025 (بزيادة 22%)، وارتفاع الترانزيت إلى سوريا بنسبة 168%، وسكة حديد العقبة إلى المناجم.']],
      ],
    },
    // ── extra national figures used by the sector slides (merged into the report data) ──
    data: {
      // young people aged 15–24 as a share of the population, 2025: UN World Population Prospects via World Bank
      // (SP.POP.1519.MA/FE.5Y + SP.POP.2024.MA/FE.5Y weighted by SP.POP.TOTL.MA/FE.IN)
      'POP.YOUTH': { value: 18.7, year: 2025 },
    },
    // sector stat cards that replace the defaults for this country
    sectorStats: {
      econ: ['SI.POV.DDAY', 'SL.UEM.TOTL.ZS', 'SL.UEM.1524.ZS', 'SL.TLF.CACT.FE.ZS', 'FX.OWN.TOTL.ZS', 'POP.YOUTH'],
    },
  },
};
if (typeof window !== 'undefined') window.COUNTRY_PACKS = COUNTRY_PACKS;
