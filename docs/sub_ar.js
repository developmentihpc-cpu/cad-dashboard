// Arabic names for DHS survey regions (report "where the need is" maps and slides).
// Keyed by the English DHS name with survey qualifiers such as "(post 2022)" removed (see subN in index.html).
// Regions not listed here keep their English name.
const AR_SUB = {
  // Angola
  'Bengo': 'بنغو', 'Benguela': 'بنغيلا', 'Bié': 'بيي', 'Cabinda': 'كابيندا', 'Cuando Cubango': 'كواندو كوبانغو',
  'Cuanza Norte': 'كوانزا الشمالية', 'Cuanza Sul': 'كوانزا الجنوبية', 'Cunene': 'كونيني', 'Huambo': 'هوامبو', 'Huíla': 'هويلا',
  'Luanda': 'لواندا', 'Lunda Norte': 'لوندا الشمالية', 'Lunda Sul': 'لوندا الجنوبية', 'Malanje': 'مالانجي', 'Moxico': 'موشيكو',
  'Namibe': 'ناميبي', 'Uíge': 'ويجي', 'Zaire': 'زائير',
  // Burkina Faso
  'Boucle de Mouhoun': 'بوكل دو موهون', 'Cascades': 'الشلالات', 'Centre (including Ouagadougou)': 'الوسط (بما فيه واغادوغو)',
  'Centre-Est': 'الوسط الشرقي', 'Centre-Nord': 'الوسط الشمالي', 'Centre-Ouest': 'الوسط الغربي', 'Centre-Sud': 'الوسط الجنوبي',
  'Hauts Bassins': 'الأحواض العليا', 'Plateau Central': 'الهضبة الوسطى', 'Sahel': 'الساحل', 'Sud-Ouest': 'الجنوب الغربي',
  // Bangladesh
  'Barishal': 'باريسال', 'Chattogram': 'شيتاغونغ', 'Dhaka': 'دكا', 'Khulna': 'خولنا', 'Mymensingh': 'ميمنسينغ',
  'Rajshahi': 'راجشاهي', 'Rangpur': 'رانغبور', 'Sylhet': 'سلهت',
  // Côte d'Ivoire
  'Abidjan': 'أبيدجان', 'Bas Sassandra': 'ساساندرا السفلى', 'Comoé': 'كوموي', 'Denguélé': 'دينغيليه', 'Goh-Djiboua': 'غوه-جيبوا',
  'Lacs': 'البحيرات', 'Lagunes': 'البحيرات الساحلية', 'Montagnes': 'الجبال', 'Sassandra-Marahoué': 'ساساندرا-ماراهوي',
  'Savanes': 'السافانا', 'Vallée du Bandama': 'وادي بانداما', 'Woroba': 'وروبا', 'Yamoussoukro': 'ياموسوكرو', 'Zanzan': 'زانزان',
  // Cameroon
  'Adamaoua': 'أداماوا', 'Douala': 'دوالا', 'Extrême-Nord': 'أقصى الشمال', 'Littoral': 'الساحل', 'Nord Ouest': 'الشمال الغربي',
  'Southwest': 'الجنوب الغربي', 'Sud Ouest': 'الجنوب الغربي', 'Yaoundé': 'ياوندي',
  // Shared compass and central names
  'Centre': 'الوسط', 'Est': 'الشرق', 'Nord': 'الشمال', 'Sud': 'الجنوب', 'Ouest': 'الغرب',
  'Central': 'الوسطى', 'Eastern': 'الشرقية', 'Northern': 'الشمالية', 'Southern': 'الجنوبية', 'Western': 'الغربية',
  'East': 'الشرقية', 'North': 'الشمالية', 'South': 'الجنوبية', 'West': 'الغربية',
  // DR Congo
  'Bas-Congo': 'الكونغو السفلى', 'Bas-Uele': 'أويلي السفلى', 'Equateur': 'الاستوائية', 'Haut-Katanga': 'كاتانغا العليا',
  'Haut-Lomani': 'لومامي العليا', 'Haut-Uele': 'أويلي العليا', 'Ituri': 'إيتوري', 'Kasai': 'كاساي', 'Kasai-Central': 'كاساي الوسطى',
  'Kasai-Oriental': 'كاساي الشرقية', 'Kinshasa': 'كينشاسا', 'Kwango': 'كوانغو', 'Kwilu': 'كويلو', 'Lomani': 'لومامي',
  'Lualaba': 'لوالابا', 'Mai-Ndombe': 'ماي-ندومبي', 'Maniema': 'مانييما', 'Mongala': 'مونغالا', 'Nord-Kivu': 'كيفو الشمالية',
  'Nord-Ubangi': 'أوبانغي الشمالية', 'Sankuru': 'سانكورو', 'Sud-Kivu': 'كيفو الجنوبية', 'Sud-Ubangi': 'أوبانغي الجنوبية',
  'Tanganyka': 'تنجانيقا', 'Tshopo': 'تشوبو', 'Tshuapa': 'تشوابا',
  // Ethiopia
  'Addis Ababa': 'أديس أبابا', 'Afar': 'عفر', 'Amhara': 'أمهرة', 'Benishangul-Gumuz': 'بني شنقول-قماز', 'Central Ethiopia': 'وسط إثيوبيا',
  'Dire Dawa': 'دير داوا', 'Gambela': 'غامبيلا', 'Harari': 'هرر', 'Oromia': 'أوروميا', 'Sidama': 'سيداما', 'Somali': 'الصومالي',
  'South Ethiopia': 'جنوب إثيوبيا', 'South West Ethiopia': 'جنوب غرب إثيوبيا', 'Tigray': 'تيغراي',
  // Ghana
  'Ahafo': 'أهافو', 'Ashanti': 'أشانتي', 'Bono': 'بونو', 'Bono East': 'بونو الشرقية', 'Greater Accra': 'أكرا الكبرى',
  'Northeast': 'الشمالية الشرقية', 'Oti': 'أوتي', 'Savannah': 'السافانا', 'Upper East': 'العليا الشرقية', 'Upper West': 'العليا الغربية',
  'Volta': 'الفولتا', 'Western North': 'الغربية الشمالية',
  // Guinea
  'Boké': 'بوكي', 'Conakry': 'كوناكري', 'Faranah': 'فاراناه', 'Kankan': 'كانكان', 'Kindia': 'كينديا', 'Labé': 'لابي',
  'Mamou': 'مامو', "N'Zérékoré": 'نزيريكوري',
  // India
  'Andaman and Nicobar Islands': 'جزر أندامان ونيكوبار', 'Andhra Pradesh': 'أندرا براديش', 'Arunachal Pradesh': 'أروناتشال براديش',
  'Assam': 'آسام', 'Bihar': 'بيهار', 'Chandigarh': 'تشانديغار', 'Chhattisgarh': 'تشاتيسغار',
  'Dadra and Nagar Haveli, Daman and Diu': 'دادرا وناغار هافيلي ودامان وديو', 'Goa': 'غوا', 'Gujarat': 'غوجارات', 'Haryana': 'هاريانا',
  'Himachal Pradesh': 'هيماجل براديش', 'Jammu & Kashmir': 'جامو وكشمير', 'Jharkhand': 'جهارخاند',
  'Karnataka': 'كارناتاكا', 'Kerala': 'كيرالا', 'Ladakh': 'لداخ', 'Lakshadweep': 'لاكشادويب', 'Madhya Pradesh': 'ماديا براديش',
  'Maharashtra': 'ماهاراشترا', 'Manipur': 'مانيبور', 'Meghalaya': 'ميغالايا', 'Mizoram': 'ميزورام', 'Nagaland': 'ناغالاند',
  'New Delhi': 'نيودلهي', 'Odisha': 'أوديشا', 'Puducherry': 'بودوتشيري', 'Punjab': 'البنجاب', 'Rajasthan': 'راجستان', 'Sikkim': 'سيكيم',
  'Tamil Nadu': 'تاميل نادو', 'Telangana': 'تيلانغانا', 'Tripura': 'تريبورا', 'Uttar Pradesh': 'أوتار براديش', 'Uttarakhand': 'أوتاراخند',
  'West Bengal': 'البنغال الغربية',
  // Jordan
  'Ajloun': 'عجلون', 'Amman': 'عمّان', 'Aqaba': 'العقبة', 'Balqa': 'البلقاء', 'Irbid': 'إربد', 'Jarash': 'جرش', 'Karak': 'الكرك',
  "Ma'an": 'معان', 'Madaba': 'مادبا', 'Mafraq': 'المفرق', 'Tafiela': 'الطفيلة', 'Zarqa': 'الزرقاء',
  // Kenya
  'Baringo': 'بارينغو', 'Bomet': 'بوميت', 'Bungoma': 'بونغوما', 'Busia': 'بوسيا', 'Elgeyo Marakwet': 'إلجيو ماراكويت', 'Embu': 'إمبو',
  'Garissa': 'غاريسا', 'Homa Bay': 'هوما باي', 'Isiolo': 'إيسيولو', 'Kajiado': 'كاجيادو', 'Kakamega': 'كاكاميغا', 'Kericho': 'كيريتشو',
  'Kiambu': 'كيامبو', 'Kilifi': 'كيليفي', 'Kirinyaga': 'كيرينياغا', 'Kisii': 'كيسي', 'Kisumu': 'كيسومو', 'Kitui': 'كيتوي',
  'Kwale': 'كوالي', 'Laikipia': 'لايكيبيا', 'Lamu': 'لامو', 'Machakos': 'ماتشاكوس', 'Makueni': 'ماكويني', 'Mandera': 'مانديرا',
  'Marsabit': 'مارسابيت', 'Meru': 'ميرو', 'Migori': 'ميغوري', 'Mombasa': 'مومباسا', "Murang'a": 'مورانغا', 'Nairobi': 'نيروبي',
  'Nakuru': 'ناكورو', 'Nandi': 'ناندي', 'Narok': 'ناروك', 'Nyamira': 'نياميرا', 'Nyandarua': 'نياندارو', 'Nyeri': 'نييري',
  'Samburu': 'سامبورو', 'Siaya': 'سيايا', 'Taita Taveta': 'تايتا تافيتا', 'Tana River': 'نهر تانا', 'Tharaka-Nithi': 'ثاراكا-نيثي',
  'Trans-Nzoia': 'ترانس نزويا', 'Turkana': 'توركانا', 'Uasin Gishu': 'واسين غيشو', 'Vihiga': 'فيهيغا', 'Wajir': 'واجير', 'West Pokot': 'بوكوت الغربية',
  // Cambodia
  'Banteay Meanchey': 'بانتياي مينشي', 'Battambang': 'باتامبانغ', 'Kampong Cham': 'كامبونغ تشام', 'Kampong Chhnang': 'كامبونغ تشنانغ',
  'Kampong Speu': 'كامبونغ سبيو', 'Kampong Thom': 'كامبونغ ثوم', 'Kampot': 'كامبوت', 'Kandal': 'كاندال', 'Kaoh Kong': 'كوه كونغ', 'Kep': 'كيب',
  'Kratie': 'كراتي', 'Mondul Kiri': 'موندولكيري', 'Otdar Mean Chey': 'أوتدار مينشي', 'Pailin': 'بايلين', 'Phnom Penh': 'بنوم بنه',
  'Preah Sihanouk': 'بريه سيهانوك', 'Preah Vihear': 'بريه فيهير', 'Prey Veng': 'بري فينغ', 'Pursat': 'بورسات', 'Ratanak Kiri': 'راتاناكيري',
  'Siem Reap': 'سيام ريب', 'Stueng Treng': 'ستونغ ترينغ', 'Svay Rieng': 'سفاي رينغ', 'Takeo': 'تاكيو', 'Tboung Khmum': 'تبونغ خموم',
  // Liberia
  'Bomi': 'بومي', 'Bong': 'بونغ', 'Gbarpolu': 'غباربولو', 'Grand Bassa': 'غراند باسا', 'Grand Cape Mount': 'غراند كيب ماونت',
  'Grand Gedeh': 'غراند جيديه', 'Grand Kru': 'غراند كرو', 'Lofa': 'لوفا', 'Margibi': 'مارغيبي', 'Maryland': 'ماريلاند', 'Monrovia': 'مونروفيا',
  'Montserrado incl. Monrovia': 'مونتسيرادو (بما فيها مونروفيا)', 'Nimba': 'نيمبا', 'North Central': 'الشمال الأوسط', 'North Western': 'الشمال الغربي',
  'River Cess': 'ريفر سيس', 'River Gee': 'ريفر جي', 'Sinoe': 'سينو', 'South Central': 'الجنوب الأوسط', 'South Eastern A': 'الجنوب الشرقي (أ)',
  'South Eastern B': 'الجنوب الشرقي (ب)',
  // Madagascar
  'Alaotra Mangoro': 'ألاوترا مانغورو', 'Analamanga excluding capital': 'أنالامانغا (عدا العاصمة)', 'Analanjirofo': 'أنالانجيروفو',
  "Anamoroni'i Mania": 'أموروني مانيا', 'Androy': 'أندروي', 'Anosy': 'أنوسي', 'Antananarivo capital': 'العاصمة أنتاناناريفو',
  'Atsimo Andrefana': 'أتسيمو أندريفانا', 'Atsimo Atsinanana': 'أتسيمو أتسينانانا', 'Atsinanana': 'أتسينانانا', 'Betsiboka': 'بيتسيبوكا',
  'Boeny': 'بويني', 'Bongolava': 'بونغولافا', 'Diana': 'ديانا', 'Haute Matsiatra': 'ماتسياترا العليا', 'Ihorombe': 'إيهورومبي',
  'Itasy': 'إيتاسي', 'Melaky': 'ميلاكي', 'Menabe': 'مينابي', 'Sava': 'سافا', 'Sofia': 'صوفيا', 'Vakinankarata': 'فاكينانكاراترا',
  'Vatovavy Fitovinany': 'فاتوفافي فيتوفيناني',
  // Mali
  'Bamako': 'باماكو', 'Gao': 'غاو', 'Kayes': 'كاي', 'Kidal': 'كيدال', 'Koulikoro': 'كوليكورو', 'Mopti': 'موبتي', 'Sikasso': 'سيكاسو',
  'Ségou': 'سيغو', 'Tombouctou': 'تمبكتو',
  // Mozambique
  'Cabo Delgado': 'كابو ديلغادو', 'Gaza': 'غازا', 'Inhambane': 'إنهامباني', 'Manica': 'مانيكا', 'Maputo Cidade': 'مدينة مابوتو',
  'Maputo Provincia': 'إقليم مابوتو', 'Nampula': 'نامبولا', 'Niassa': 'نياسا', 'Sofala': 'سوفالا', 'Tete': 'تيتي', 'Zambézia': 'زامبيزيا',
  // Mauritania
  'Adrar': 'آدرار', 'Assaba': 'العصابة', 'Brakna': 'البراكنة', 'Dakhlet Nouadhibou': 'داخلت نواذيبو', 'Gorgol': 'كوركول',
  'Guidimagha': 'كيدي ماغا', 'Hodh Echargui': 'الحوض الشرقي', 'Hodh Gharbi': 'الحوض الغربي', 'Nouakchott Nord': 'نواكشوط الشمالية',
  'Nouakchott Ouest': 'نواكشوط الغربية', 'Nouakchott Sud': 'نواكشوط الجنوبية', 'Tagant': 'تكانت', 'Tiris Zemour et Inchiri': 'تيرس زمور وإينشيري',
  'Trarza': 'الترارزة',
  // Malawi
  'Balaka': 'بالاكا', 'Blantyre': 'بلانتاير', 'Blantyre City': 'مدينة بلانتاير', 'Chikwawa': 'تشيكواوا', 'Chiradzulu': 'تشيرادزولو',
  'Chitipa': 'تشيتيبا', 'Dedza': 'ديدزا', 'Dowa': 'دوا', 'Karonga': 'كارونغا', 'Kasungu': 'كاسونغو', 'Likoma': 'ليكوما', 'Lilongwe': 'ليلونغوي',
  'Lilongwe City': 'مدينة ليلونغوي', 'Machinga': 'ماتشينغا', 'Mangochi': 'مانغوتشي', 'Mchinji': 'مشينجي', 'Mulanje': 'مولانجي',
  'Mwanza': 'موانزا', 'Mzimba': 'مزيمبا', 'Mzuzu City': 'مدينة مزوزو', 'Neno': 'نينو', 'Nkhata Bay': 'نخاتا باي', 'Nkhotakota': 'نخوتاكوتا',
  'Nsanje': 'نسانجي', 'Ntcheu': 'نتشيو', 'Ntchisi': 'نتشيسي', 'Phalombe': 'فالومبي', 'Rumphi': 'رومفي', 'Salima': 'ساليما', 'Thyolo': 'تيولو',
  'Zomba': 'زومبا', 'Zomba City': 'مدينة زومبا',
  // Niger
  'Agadez': 'أغاديس', 'Diffa': 'ديفا', 'Dosso': 'دوسو', 'Maradi': 'مارادي', 'Niamey': 'نيامي', 'Tahoua': 'تاهوا', 'Tillabéri': 'تيلابيري',
  'Zinder': 'زندر',
  // Nigeria
  'Abia': 'أبيا', 'Adamawa': 'أداماوا', 'Akwa Ibom': 'أكوا إيبوم', 'Anambra': 'أنامبرا', 'Bauchi': 'باوتشي', 'Bayelsa': 'بايلسا',
  'Benue': 'بينوي', 'Borno': 'بورنو', 'Cross River': 'كروس ريفر', 'Delta': 'دلتا', 'Ebonyi': 'إيبونيي', 'Edo': 'إيدو', 'Ekiti': 'إكيتي',
  'Enugu': 'إينوغو', 'FCT Abuja': 'إقليم العاصمة أبوجا', 'Gombe': 'غومبي', 'Imo': 'إيمو', 'Jigawa': 'جيغاوا', 'Kaduna': 'كادونا',
  'Kano': 'كانو', 'Katsina': 'كاتسينا', 'Kebbi': 'كيبي', 'Kogi': 'كوغي', 'Kwara': 'كوارا', 'Lagos': 'لاغوس', 'Nasarawa': 'ناساراوا',
  'Niger': 'النيجر', 'Ogun': 'أوغون', 'Ondo': 'أوندو', 'Osun': 'أوسون', 'Oyo': 'أويو', 'Plateau': 'بلاتو', 'Rivers': 'ريفرز',
  'Sokoto': 'سوكوتو', 'Taraba': 'تارابا', 'Yobe': 'يوبي', 'Zamfara': 'زامفارا',
  // Nepal
  'Bagmati province': 'مقاطعة باغماتي', 'Gandaki province': 'مقاطعة غانداكي', 'Karnali province': 'مقاطعة كارنالي',
  'Koshi province': 'مقاطعة كوشي', 'Lumbini province': 'مقاطعة لومبيني', 'Madhesh province': 'مقاطعة ماديش',
  'Sudurpashchim province': 'مقاطعة سودورباشيم',
  // Philippines
  'BARMM': 'بانغسامورو', 'Bicol': 'بيكول', 'CALABARAZON': 'كالابارزون', 'Cagayan Valley': 'وادي كاغايان', 'Caraga': 'كاراغا',
  'Central Luzon': 'لوزون الوسطى', 'Central Visayas': 'فيساياس الوسطى', 'Cordillera Administ.': 'منطقة كورديليرا', 'Davao': 'دافاو',
  'Eastern Visayas': 'فيساياس الشرقية', 'Ilocos': 'إيلوكوس', 'MIMAROPA': 'ميماروبا', 'National Capital Region': 'منطقة العاصمة الوطنية',
  'Northern Mindanao': 'مينداناو الشمالية', 'SOCCSKSARGEN': 'سوكسكسارجن', 'Western Visayas': 'فيساياس الغربية',
  'Zamboanga Peninsula': 'شبه جزيرة زامبوانغا',
  // Rwanda
  'Kigali': 'كيغالي',
  // Senegal
  'Dakar': 'داكار', 'Diourbel': 'جوربل', 'Fatick': 'فاتيك', 'Kaffrine': 'كافرين', 'Kaolack': 'كاولاك', 'Kolda': 'كولدا', 'Kédougou': 'كيدوغو',
  'Louga': 'لوغا', 'Matam': 'ماتام', 'Saint Louis': 'سان لويس', 'Sédhiou': 'سيديو', 'Tambacounda': 'تامباكوندا', 'Thiès': 'تييس',
  'Ziguinchor': 'زيغنشور',
  // Sierra Leone
  'Bo': 'بو', 'Bombali': 'بومبالي', 'Bonthe': 'بونثي', 'Falaba': 'فالابا', 'Kailahun': 'كايلاهون', 'Kambia': 'كامبيا', 'Karene': 'كارين',
  'Kenema': 'كينيما', 'Koinadugu': 'كويناديوغو', 'Kono': 'كونو', 'Moyamba': 'مويامبا', 'Port Loko': 'بورت لوكو', 'Pujehun': 'بوجيهون',
  'Tonkolili': 'تونكوليلي', 'Western Rural': 'الغربية الريفية', 'Western Urban': 'الغربية الحضرية',
  // Tajikistan
  'DRS': 'مناطق الخضوع الجمهوري', 'Dushanbe': 'دوشنبه', 'GBAO': 'غورنو-باداخشان', 'Khatlon': 'ختلان', 'Sughd': 'صغد',
  // Tanzania
  'Arusha': 'أروشا', 'Dar es Salaam': 'دار السلام', 'Dodoma': 'دودوما', 'Geita': 'غيتا', 'Iringa': 'إيرينغا', 'Kagera': 'كاغيرا',
  'Kaskazini Pemba': 'بيمبا الشمالية', 'Kaskazini Unguja': 'أونغوجا الشمالية', 'Katavi': 'كاتافي', 'Kigoma': 'كيغوما',
  'Kilimanjaro': 'كليمنجارو', 'Kusini Pemba': 'بيمبا الجنوبية', 'Kusini Unguja': 'أونغوجا الجنوبية', 'Lindi': 'ليندي', 'Manyara': 'مانيارا',
  'Mara': 'مارا', 'Mbeya': 'مبيا', 'Mjini Magharibi': 'مجيني ماغاريبي', 'Morogoro': 'موروغورو', 'Mtwara': 'متوارا', 'Njombe': 'نجومبي',
  'Pwani': 'بواني', 'Rukwa': 'روكوا', 'Ruvuma': 'روفوما', 'Shinyanga': 'شينيانغا', 'Simiyu': 'سيميو', 'Singida': 'سينغيدا', 'Songwe': 'سونغوي',
  'Tabora': 'تابورا', 'Tanga': 'تانغا',
  // Uganda
  'Acholi': 'أتشولي', 'Ankole': 'أنكولي', 'Bugisu/Elgon': 'بوغيسو/إلغون', 'Bukedi': 'بوكيدي', 'Bunyoro': 'بونيورو', 'Busoga': 'بوسوغا',
  'Kampala': 'كمبالا', 'Karamoja': 'كاراموجا', 'Kigezi': 'كيغيزي', 'Lango': 'لانغو', 'North Buganda': 'بوغندا الشمالية',
  'South Buganda': 'بوغندا الجنوبية', 'Teso': 'تيسو', 'Tooro': 'تورو', 'West Nile': 'غرب النيل',
  // Zambia
  'Copperbelt': 'كوبربلت', 'Luapula': 'لوابولا', 'Lusaka': 'لوساكا', 'Muchinga': 'موتشينغا', 'North-Western': 'الشمالية الغربية',
};
