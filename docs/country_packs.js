/* country_packs.js — extra, researched slides for selected countries (English + Arabic).
 * A pack adds: context (what drives need · development opportunities) after the executive summary; a governorate
 * atlas (two maps per slide) after the sector slides; a sector-by-sector view for each focus area (focus_areas.js);
 * and a recommendations slide before the method slide. Content is dated (asOf) — review it when sources update.
 * Map values are keyed by the region names in data/subnational/{ISO3}.json (the outlines come from there).
 * Every text is [English, Arabic].
 */
'use strict';
const COUNTRY_PACKS = {
  Jordan: {
    asOf: '2026-11',
    // ── context: what drives need ──
    drivers: {
      facts: [
        ['21.4%', ['Unemployment among Jordanians', 'البطالة بين الأردنيين'], ['Q3 2025 · women 33.9%, men 18.0%', 'الربع الثالث 2025 · النساء 33.9% والرجال 18.0%']],
        ['14.4%', ["Women's labour-force participation", 'مشاركة المرأة في القوى العاملة'], ['Q3 2025 · Arab average 18.1%', 'الربع الثالث 2025 · المتوسط العربي 18.1%']],
        ['61 m³', ['Renewable water per person a year', 'المياه المتجددة للفرد سنوياً'], ['Absolute scarcity line: 500 m³', 'خط الشح المطلق: 500 م³']],
        ['388,505', ['Registered Syrian refugees', 'اللاجئون السوريون المسجلون'], ['UNHCR, 30 Apr 2026 · 21% in camps', 'المفوضية، 30 أبريل 2026 · 21% في المخيمات']],
        ['108%', ['Public debt, % of GDP (2026)', 'الدين العام (% من الناتج، 2026)'], ['IMF · 82% net of Social Security holdings', 'صندوق النقد · 82% بعد استبعاد حيازات الضمان الاجتماعي']],
      ],
      points: [
        [['Jobs', 'فرص العمل'], ['One in five Jordanians in the labour force is unemployed, and one in three women; only one woman in seven is in the labour force. Unemployment is highest in Ma\'an (29.4%), Jerash (27.3%), Balqa (26.4%) and Irbid (24.9%).',
          'عاطل واحد من كل خمسة أردنيين في القوى العاملة، وواحدة من كل ثلاث نساء؛ ولا تشارك في سوق العمل سوى امرأة واحدة من كل سبع. وتبلغ البطالة أعلى مستوياتها في معان (29.4%) وجرش (27.3%) والبلقاء (26.4%) وإربد (24.9%).']],
        [['Water', 'المياه'], ['Jordan is among the most water-scarce countries in the world, and close to half of piped water is lost to leaks, theft and metering errors; the National Water Carrier from Aqaba is due in 2030.',
          'الأردن من أشد دول العالم شحاً في المياه، ويُفقد نحو نصف المياه المنقولة بالشبكات بسبب التسرب والسرقة وأخطاء القياس؛ ويُنتظر تشغيل ناقل المياه الوطني من العقبة في 2030.']],
        [['Refugee hosting', 'استضافة اللاجئين'], ['Jordan hosts 388,505 registered Syrian refugees — nearly 80% in towns and cities, mostly Amman, Irbid, Mafraq and Zarqa — alongside about 2.4 million registered Palestine refugees, which stretches schools, clinics and water.',
          'يستضيف الأردن 388,505 لاجئين سوريين مسجلين، نحو 80% منهم في المدن والبلدات، ولا سيما عمّان وإربد والمفرق والزرقاء، إلى جانب نحو 2.4 مليون لاجئ فلسطيني مسجل، ما يضغط على المدارس والعيادات والمياه.']],
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
      { title: ['Jobs and refugee hosting', 'فرص العمل واستضافة اللاجئين'],
        statement: ['unemployment peaks in the south and north; refugees concentrate in the north and centre', 'البطالة أعلى في الجنوب والشمال، واللاجئون يتركزون في الشمال والوسط'],
        maps: ['unemp', 'refugees'] },
      { title: ['Child health', 'صحة الطفل'],
        statement: ["vaccination gaps in Ma'an, Madaba and Aqaba; stunting highest in Mafraq and Ma'an", 'فجوات التحصين في معان ومادبا والعقبة، والتقزّم أعلى في المفرق ومعان'],
        maps: ['vacc', 'stunt'] },
      { title: ['Nutrition — anaemia', 'التغذية — فقر الدم'],
        statement: ['anaemia among women and children is concentrated in the northern governorates', 'يتركز فقر الدم بين النساء والأطفال في محافظات الشمال'],
        maps: ['anemW', 'anemC'] },
    ],
    maps: {
      unemp: { name: ['Unemployment among Jordanians', 'البطالة بين الأردنيين'], unit: '%', worse: 'high', national: 21.4,
        source: ['DoS Labour Force Survey, Q3 2025', 'مسح القوى العاملة، الربع الثالث 2025'],
        values: { Amman: 19.5, Balqa: 26.4, Zarqa: 18.2, Madaba: 21.4, Irbid: 24.9, Mafraq: 24.3, Jarash: 27.3, Ajloun: 20.6, Karak: 17.3, Tafiela: 19.0, "Ma'an": 29.4, Aqaba: 18.9 },
        reading: ["Highest in Ma'an (29.4%, eight points above the national rate) and Jerash (27.3%); lowest in Karak (17.3%).",
                  'الأعلى في معان (29.4%، أي ثماني نقاط فوق المعدل الوطني) وجرش (27.3%)؛ والأدنى في الكرك (17.3%).'] },
      refugees: { name: ['Registered Syrian refugees', 'اللاجئون السوريون المسجلون'], unit: 'count', worse: 'high', national: null,
        source: ['UNHCR, 30 Apr 2026 · camps counted in their governorate', 'المفوضية، 30 أبريل 2026 · المخيمات ضمن محافظاتها'],
        values: { Amman: 122704, Irbid: 68225, Mafraq: 99418, Zarqa: 57222, Balqa: 10562, Madaba: 8122, "Ma'an": 5895, Karak: 4932, Jarash: 4478, Ajloun: 2902, Aqaba: 2746, Tafiela: 883 },
        reading: ['Amman (122,704), Mafraq (99,418, including Zaatari camp) and Irbid (68,225) host 75% of registered Syrian refugees; Zarqa includes Azraq camp.',
                  'تستضيف عمّان (122,704) والمفرق (99,418 بما فيها مخيم الزعتري) وإربد (68,225) 75% من اللاجئين السوريين المسجلين؛ وتشمل الزرقاء مخيم الأزرق.'] },
      vacc: { dhs: 'health', name: ['Children with all basic vaccinations', 'الأطفال الحاصلون على جميع التطعيمات الأساسية'], unit: '%', worse: 'low',
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        reading: ["Ma'an (69.6%) and Madaba (80.8%) lag far behind the national 91.7%; Aqaba (84.1%) is third-lowest.",
                  'تتأخر معان (69.6%) ومادبا (80.8%) كثيراً عن المعدل الوطني البالغ 91.7%، وتأتي العقبة (84.1%) في المرتبة الثالثة من الأدنى.'] },
      stunt: { dhs: 'food', name: ['Child stunting (under 5)', 'تقزّم الأطفال دون الخامسة'], unit: '%', worse: 'high',
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        reading: ["Mafraq (15.2%), Ma'an (13.0%) and Tafiela (12.7%) are above 10%, the WHO threshold for a medium public-health concern; the national rate is 8.3%.",
                  'تتجاوز المفرق (15.2%) ومعان (13.0%) والطفيلة (12.7%) نسبة 10%، وهي عتبة منظمة الصحة العالمية لمشكلة صحة عامة متوسطة، فيما يبلغ المعدل الوطني 8.3%.'] },
      anemW: { name: ['Women with anaemia', 'النساء المصابات بفقر الدم'], unit: '%', worse: 'high', national: 32.3,
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        values: { Amman: 27.0, Balqa: 29.2, Zarqa: 27.8, Madaba: 30.9, Irbid: 41.2, Mafraq: 48.5, Jarash: 51.4, Ajloun: 40.1, Karak: 33.2, Tafiela: 42.0, "Ma'an": 46.1, Aqaba: 35.8 },
        reading: ["About half of women in Jerash (51.4%) and Mafraq (48.5%) are anaemic, against 32.3% nationally — a severe public-health problem by WHO's 40% line.",
                  'تعاني نحو نصف النساء في جرش (51.4%) والمفرق (48.5%) من فقر الدم، مقابل 32.3% على المستوى الوطني، وهي مشكلة صحة عامة حادة وفق عتبة منظمة الصحة العالمية البالغة 40%.'] },
      anemC: { name: ['Children with anaemia', 'الأطفال المصابون بفقر الدم'], unit: '%', worse: 'high', national: 32.0,
        source: ['Jordan Population and Family Health Survey (DHS) 2023', 'مسح السكان والصحة الأسرية (DHS) 2023'],
        values: { Amman: 27.5, Balqa: 35.3, Zarqa: 27.3, Madaba: 25.6, Irbid: 42.7, Mafraq: 44.6, Jarash: 44.1, Ajloun: 37.6, Karak: 31.5, Tafiela: 28.8, "Ma'an": 18.3, Aqaba: 33.1 },
        reading: ['Highest in Mafraq (44.6%), Jarash (44.1%) and Irbid (42.7%) — the same northern governorates that host most refugees.',
                  'الأعلى في المفرق (44.6%) وجرش (44.1%) وإربد (42.7%)، وهي محافظات الشمال نفسها التي تستضيف معظم اللاجئين.'] },
    },
    // ── focus area sector by sector (by focus key) ──
    focusSectors: {
      aqaba: [
        // [sector EN/AR, rating 'strength'|'mixed'|'gap', text EN/AR]
        [['Water', 'المياه'], 'strength', ['Hub of the National Water Carrier (50 million m³ a year reserved for Aqaba); every household uses an improved water source (DHS 2023).',
          'مركز ناقل المياه الوطني (50 مليون م³ سنوياً مخصصة للعقبة)؛ وتستخدم جميع الأسر مصدر مياه محسّناً (2023).']],
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
    // ── recommendations ──
    recommendations: {
      priorities: [
        [['Jobs for young people and women', 'فرص العمل للشباب والنساء'], ["Target Ma'an, Jerash, Balqa and Irbid (unemployment 24–29%). Link vocational training, wage subsidies and childcare to employers in the national projects; women's unemployment is 33.9%.",
          'استهداف معان وجرش والبلقاء وإربد (بطالة 24–29%)، وربط التدريب المهني ودعم الأجور ورعاية الأطفال بأصحاب العمل في المشاريع الوطنية؛ إذ تبلغ بطالة النساء 33.9%.']],
        [['Water security', 'الأمن المائي'], ['Back the National Water Carrier and cut non-revenue water (close to half of supply) in the north, where refugee hosting adds demand.',
          'دعم ناقل المياه الوطني وخفض الفاقد المائي (نحو نصف الإمدادات) في الشمال، حيث تزيد استضافة اللاجئين الطلب.']],
        [['Host communities', 'المجتمعات المضيفة'], ['Strengthen schools, clinics and municipal services in Amman, Irbid, Mafraq and Zarqa, which host most refugees, as humanitarian funding falls.',
          'تعزيز المدارس والعيادات والخدمات البلدية في عمّان وإربد والمفرق والزرقاء التي تستضيف معظم اللاجئين، مع تراجع التمويل الإنساني.']],
        [['Child health and nutrition', 'صحة الطفل والتغذية'], ["Close vaccination gaps in Ma'an, Madaba and Aqaba; tackle anaemia and stunting in Mafraq, Jerash and Ma'an through iron supplementation, fortification and maternal nutrition.",
          'سدّ فجوات التحصين في معان ومادبا والعقبة، ومعالجة فقر الدم والتقزّم في المفرق وجرش ومعان عبر مكملات الحديد وتدعيم الأغذية وتغذية الأمهات.']],
      ],
      investment: [
        ['Co-invest in the national projects with established UAE links: the Aqaba railway, the port and logistics, and green hydrogen and ammonia.',
         'الاستثمار المشترك في المشاريع الوطنية ذات الروابط الإماراتية القائمة: سكة حديد العقبة، والميناء والخدمات اللوجستية، والهيدروجين والأمونيا الخضراء.'],
        ['Blended finance alongside the National Water Carrier for distribution networks and leak reduction.',
         'تمويل مختلط إلى جانب ناقل المياه الوطني لشبكات التوزيع والحد من التسرب.'],
        ['Digital and data-centre investment around the Aqaba Digital Hub, with skills programmes for young Jordanians.',
         'الاستثمار الرقمي ومراكز البيانات حول مركز العقبة الرقمي، مع برامج مهارات للشباب الأردني.'],
      ],
      sources: ['Jordan DoS · UNHCR · DHS 2023 · IMF · Ministry of Planning · AD Ports Group · EU · EBRD',
                'الإحصاءات العامة · المفوضية · المسح الصحي 2023 · صندوق النقد · وزارة التخطيط · موانئ أبوظبي · الاتحاد الأوروبي · البنك الأوروبي'],
    },
  },
};
if (typeof window !== 'undefined') window.COUNTRY_PACKS = COUNTRY_PACKS;
