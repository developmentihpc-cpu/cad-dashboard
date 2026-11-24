/* focus_areas.js — sub-national "focus areas" added to a country's report (English + Arabic).
 * A focus area is marked on the report's country map and gets its own slides (overview, sector snapshot,
 * where support is needed), placed after the sector slides. Content is researched and dated: review it when
 * the sources update. `dhs` names the area as it appears in data/subnational/{ISO3}.json, so the survey
 * figures (area vs national) come from the same data as the "where the need is" maps.
 * Every text is [English, Arabic].
 */
'use strict';
const FOCUS_AREAS = {
  Jordan: [{
    key: 'aqaba',
    name: ['Al Aqabah', 'العقبة'],
    ll: [29.532, 35.006],                       // Aqaba city
    dhs: 'Aqaba',                               // governorate name in the DHS survey file
    asOf: '2026-11',
    tagline: ["Jordan's gateway to the Red Sea", 'بوابة الأردن على البحر الأحمر'],
    facts: [
      ['188,160', ['Population (2015 census)', 'عدد السكان (تعداد 2015)'], ['Aqaba governorate · new census due 2026', 'محافظة العقبة · تعداد جديد في 2026']],
      ['17.3%', ['Unemployment, 2024', 'معدل البطالة، 2024'], ['Lowest of the 12 governorates (national 21.4%)', 'الأدنى بين المحافظات الاثنتي عشرة (الوطني 21.4%)']],
      [['1.0M TEU', '1.0 مليون حاوية'], ['Containers handled, 2025', 'الحاويات المناولة، 2025'], ['Aqaba ports · up 22% on 2024', 'موانئ العقبة · بزيادة 22% عن 2024']],
      ['61,000', ['Jobs in the economic zone', 'الوظائف في المنطقة الاقتصادية'], ['ASEZA, 2025 · 10,000+ private-sector jobs since 2018', 'سلطة المنطقة، 2025 · أكثر من 10,000 وظيفة في القطاع الخاص منذ 2018']],
    ],
    overview: [
      ["Jordan's only seaport and its gateway to the Red Sea, handling most of the country's sea-borne trade and transit cargo for Iraq and, increasingly, Syria (transit containers rose 168% in 2025).",
       'الميناء البحري الوحيد في الأردن وبوابته على البحر الأحمر، إذ يتولى معظم تجارة المملكة البحرية وبضائع الترانزيت المتجهة إلى العراق، وبصورة متزايدة إلى سوريا (ارتفعت حاويات الترانزيت بنسبة 168% في 2025).'],
      ['Governed since 2001 as the Aqaba Special Economic Zone (ASEZ) by the Aqaba Special Economic Zone Authority, with tax and customs incentives; its priority sectors are industry, information technology and tourism.',
       'تُدار منذ عام 2001 بوصفها منطقة العقبة الاقتصادية الخاصة تحت إشراف سلطة منطقة العقبة الاقتصادية الخاصة، مع حوافز ضريبية وجمركية؛ وقطاعاتها ذات الأولوية هي الصناعة وتقنية المعلومات والسياحة.'],
      ['Anchor of the "Golden Triangle" of Aqaba, Petra and Wadi Rum: about 300,000 people visited Wadi Rum in 2025, and Aqaba\'s festivals and events drew more than one million visitors.',
       'محور «المثلث الذهبي» الذي يضم العقبة والبتراء ووادي رم: زار وادي رم نحو 300,000 شخص في 2025، واستقطبت مهرجانات العقبة وفعالياتها أكثر من مليون زائر.'],
      ['Hosts the national strategic water project: the Aqaba–Amman Water Desalination and Conveyance Project will desalinate Red Sea water at Aqaba and pump it 438 km north to Amman.',
       'تحتضن المشروع الوطني الاستراتيجي للمياه: مشروع ناقل المياه الوطني (العقبة–عمّان) لتحلية مياه البحر الأحمر في العقبة وضخّها مسافة 438 كم شمالاً إلى عمّان.'],
    ],
    sectors: [
      [['Ports & logistics', 'الموانئ والخدمات اللوجستية'],
       ['Record year in 2025: 1.0 million TEU of containers (+22%), 15.0 million tonnes of dry bulk (+4%) and 6.2 million tonnes of liquid bulk. AD Ports Group (UAE) signed a 30-year concession for the Aqaba Multipurpose Port in February 2026 — a 70/30 joint venture with the Aqaba Development Corporation, AED 141 million (US$38 million) of investment, operations from August 2026, capacity 11 million tonnes a year.',
        'عام قياسي في 2025: مليون حاوية نمطية (بزيادة 22%)، و15.0 مليون طن من البضائع السائبة الجافة (بزيادة 4%)، و6.2 مليون طن من السوائب السائلة. ووقّعت مجموعة موانئ أبوظبي في فبراير 2026 امتيازاً لمدة 30 عاماً لتشغيل ميناء العقبة متعدد الأغراض، عبر مشروع مشترك مع شركة تطوير العقبة بنسبة 70/30 واستثمار قدره 141 مليون درهم (38 مليون دولار)، على أن يبدأ التشغيل في أغسطس 2026 بطاقة 11 مليون طن سنوياً.']],
      [['Water', 'المياه'],
       ['Jordan is among the most water-scarce countries in the world. The National Water Carrier will desalinate 300 million m³ a year at Aqaba — 250 million for Amman and 50 million for Aqaba — powered partly by a 281 MW solar plant. A 30-year concession was signed in January 2025 (Meridiam and SUEZ); financing approved in 2025–26 includes the Green Climate Fund, AIIB and a US grant.',
        'الأردن من أكثر دول العالم شحّاً في المياه. وسيُحلّي ناقل المياه الوطني 300 مليون متر مكعب سنوياً في العقبة، منها 250 مليوناً لعمّان و50 مليوناً للعقبة، بالاعتماد جزئياً على محطة طاقة شمسية بقدرة 281 ميغاواط. ووُقّع امتياز لمدة 30 عاماً في يناير 2025 (ميريديام وسويز)، ويشمل التمويل المعتمد في 2025–2026 صندوق المناخ الأخضر والبنك الآسيوي للاستثمار في البنية التحتية ومنحة أمريكية.']],
      [['Tourism', 'السياحة'],
       ['Red Sea coast, diving and the Wadi Rum desert make tourism a major employer, but visitor numbers are sensitive to regional conflict; ASEZA waived rent and licence fees for certified desert camps in 2024–25 and introduced new investment incentives in 2026.',
        'يجعل ساحل البحر الأحمر والغوص وصحراء وادي رم السياحة من أكبر مصادر التشغيل، غير أن أعداد الزوار تتأثر بالنزاعات الإقليمية؛ وقد أعفت سلطة المنطقة المخيمات الصحراوية الحاصلة على الشهادة الخضراء من الإيجار ورسوم الترخيص في 2024–2025، وأطلقت حوافز استثمارية جديدة في 2026.']],
      [['Jobs', 'فرص العمل'],
       ['Unemployment of 17.3% (2024) is the lowest in Jordan but still high; growth in ports, logistics and tourism needs a matching supply of skilled local workers.',
        'تبلغ البطالة 17.3% (2024)، وهي الأدنى في الأردن لكنها لا تزال مرتفعة؛ ويتطلب نمو الموانئ والخدمات اللوجستية والسياحة توفير أيدٍ عاملة محلية ماهرة بما يكفي.']],
    ],
    needs: [
      ['Child immunisation: 84% of children have all basic vaccinations, against 92% nationally — the third-lowest of the 12 governorates (2023). Outreach to mobile and migrant-worker families and to remote desert communities (Wadi Rum, Al Quwayrah).',
       'تحصين الأطفال: 84% من الأطفال تلقّوا جميع اللقاحات الأساسية مقابل 92% على المستوى الوطني، وهي ثالث أدنى نسبة بين المحافظات الاثنتي عشرة (2023). ويُوصى بالوصول إلى الأسر المتنقلة وأسر العمال الوافدين والمجتمعات الصحراوية النائية (وادي رم والقويرة).'],
      ['Skills for the special economic zone: technical and vocational training linked to employers in ports, logistics, tourism and IT, with places reserved for young people and women.',
       'المهارات لخدمة المنطقة الاقتصادية الخاصة: تدريب تقني ومهني مرتبط بأصحاب العمل في الموانئ والخدمات اللوجستية والسياحة وتقنية المعلومات، مع تخصيص مقاعد للشباب والنساء.'],
      ['Coast and water: protect the Gulf of Aqaba\'s coral reefs and marine environment as desalination and port capacity expand, and make sure Aqaba\'s own supply benefits from the National Water Carrier.',
       'الساحل والمياه: حماية الشعاب المرجانية والبيئة البحرية في خليج العقبة مع توسع طاقة التحلية والموانئ، وضمان استفادة العقبة نفسها من ناقل المياه الوطني.'],
      ['Tourism livelihoods: small-business finance and diversification for tour operators, desert camps and guides, so incomes withstand regional shocks.',
       'سبل العيش السياحية: تمويل المشروعات الصغيرة وتنويع الأنشطة لمنظمي الرحلات والمخيمات الصحراوية والأدلّاء، لتصمد الدخول أمام الصدمات الإقليمية.'],
    ],
    invest: [
      ['Ports and logistics: build on AD Ports Group\'s concession with logistics parks, Ro-Ro and cold-chain facilities for transit trade to Iraq and Syria.',
       'الموانئ والخدمات اللوجستية: البناء على امتياز مجموعة موانئ أبوظبي عبر مجمّعات لوجستية ومرافق للدحرجة وسلاسل التبريد لخدمة تجارة الترانزيت إلى العراق وسوريا.'],
      ['Water and energy: co-investment alongside the National Water Carrier — solar generation, water storage and distribution in Aqaba.',
       'المياه والطاقة: الاستثمار المشترك إلى جانب ناقل المياه الوطني في توليد الطاقة الشمسية وتخزين المياه وتوزيعها في العقبة.'],
      ['Tourism: coastal hospitality and eco-tourism in Wadi Rum, with local-employment commitments.',
       'السياحة: الضيافة الساحلية والسياحة البيئية في وادي رم، مع التزامات بتشغيل أبناء المنطقة.'],
    ],
    verdict: ['Al Aqabah is one of Jordan\'s better-performing governorates — the lowest unemployment and near-universal water and literacy — so support should target the specific gaps below rather than broad-based need.',
              'تُعد العقبة من أفضل المحافظات أداءً في الأردن، إذ تسجّل أدنى معدل للبطالة وتغطية شبه شاملة لمياه الشرب ومعرفة القراءة والكتابة؛ لذا ينبغي أن يستهدف الدعم الفجوات المحددة أدناه لا الاحتياجات العامة.'],
    sources: ['Jordan DoS · ASEZA · Jordan Shipping Association · APM Terminals · AD Ports Group · GCF · AIIB · DHS 2023 · Petra',
              'الإحصاءات العامة · سلطة العقبة الاقتصادية · جمعية ملاحة الأردن · إيه بي إم تيرمينالز · موانئ أبوظبي · صندوق المناخ الأخضر · البنك الآسيوي · المسح الصحي 2023 · بترا'],
  }],
};
if (typeof window !== 'undefined') window.FOCUS_AREAS = FOCUS_AREAS;
