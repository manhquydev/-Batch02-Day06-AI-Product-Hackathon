import type { ChatResponse, Movie, ReasoningStep } from "./types";

  // Deterministic hue per title so poster gradients stay stable.
  function hue(str: string): number {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) % 360;
    return h;
  }

  // poster: {h1,h2} duotone seeds derived from title
  function mk(o: Omit<Movie, "h1" | "h2"> & { title: string }): Movie {
    const h = hue(o.title);
    return Object.assign({ h1: h, h2: (h + 38) % 360 }, o) as Movie;
  }

  const M = {
    inception:  mk({ id:27205, title:"Inception", year:2010, rating:8.4, genres:["Khoa học viễn tưởng","Hành động"], netflix:true,
                     overview:"Một tên trộm chuyên đánh cắp bí mật từ tiềm thức được giao nhiệm vụ cấy ghép một ý tưởng." }),
    interstellar: mk({ id:157336, title:"Interstellar", year:2014, rating:8.4, genres:["Khoa học viễn tưởng","Chính kịch"], netflix:true,
                     overview:"Nhóm phi hành gia du hành qua hố sâu không-thời gian để tìm hành tinh mới cho nhân loại." }),
    tenet:      mk({ id:577922, title:"Tenet", year:2020, rating:7.3, genres:["Khoa học viễn tưởng","Hành động"], netflix:false,
                     overview:"Một điệp viên thao túng dòng chảy thời gian để ngăn chặn Thế chiến thứ ba." }),
    shutter:    mk({ id:11324, title:"Shutter Island", year:2010, rating:8.2, genres:["Bí ẩn","Giật gân"], netflix:true,
                     overview:"Hai cảnh sát điều tra vụ mất tích tại một bệnh viện tâm thần trên hòn đảo biệt lập." }),
    prestige:   mk({ id:1124, title:"The Prestige", year:2006, rating:8.5, genres:["Bí ẩn","Chính kịch"], netflix:false,
                     overview:"Hai ảo thuật gia lao vào cuộc đối đầu ám ảnh để tạo ra màn ảo thuật hoàn hảo." }),
    dune2:      mk({ id:693134, title:"Dune: Part Two", year:2024, rating:8.3, genres:["Khoa học viễn tưởng","Phiêu lưu"], netflix:false,
                     overview:"Paul Atreides liên minh với người Fremen để báo thù và ngăn một tương lai khủng khiếp." }),
    arrival:    mk({ id:329865, title:"Arrival", year:2016, rating:7.9, genres:["Khoa học viễn tưởng","Chính kịch"], netflix:true,
                     overview:"Một nhà ngôn ngữ học tìm cách giao tiếp với người ngoài hành tinh vừa đáp xuống Trái Đất." }),
    br2049:     mk({ id:335984, title:"Blade Runner 2049", year:2017, rating:8.0, genres:["Khoa học viễn tưởng","Giật gân"], netflix:false,
                     overview:"Một blade runner trẻ khám phá bí mật bị chôn giấu có thể đẩy xã hội vào hỗn loạn." }),
    matrix:     mk({ id:603, title:"The Matrix", year:1999, rating:8.2, genres:["Khoa học viễn tưởng","Hành động"], netflix:true,
                     overview:"Một hacker phát hiện sự thật chấn động về thực tại và vai trò của mình trong cuộc chiến." }),
    edgeoftom:  mk({ id:137113, title:"Edge of Tomorrow", year:2014, rating:7.9, genres:["Khoa học viễn tưởng","Hành động"], netflix:false,
                     overview:"Một sĩ quan mắc kẹt trong vòng lặp thời gian, sống và chết lặp lại trong trận chiến với người ngoài hành tinh." }),

    // feel-good / light
    amelie:     mk({ id:194, title:"Amélie", year:2001, rating:8.3, genres:["Lãng mạn","Hài"], netflix:false,
                     overview:"Cô gái nhút nhát ở Paris âm thầm thay đổi cuộc đời những người xung quanh." }),
    paddington2:mk({ id:346648, title:"Paddington 2", year:2017, rating:8.0, genres:["Gia đình","Hài"], netflix:true,
                     overview:"Chú gấu Paddington lan tỏa lòng tốt khắp khu phố trong khi tìm món quà sinh nhật cho dì Lucy." }),
    grandbud:   mk({ id:120467, title:"The Grand Budapest Hotel", year:2014, rating:8.1, genres:["Hài","Phiêu lưu"], netflix:false,
                     overview:"Cuộc phiêu lưu rực rỡ của một quản lý khách sạn huyền thoại và cậu nhân viên trung thành." }),
    chef:       mk({ id:213121, title:"Chef", year:2014, rating:7.3, genres:["Hài","Chính kịch"], netflix:true,
                     overview:"Một đầu bếp bỏ nhà hàng cao cấp để mở xe bán đồ ăn và tìm lại đam mê." }),
    littlemiss: mk({ id:773, title:"Little Miss Sunshine", year:2006, rating:7.8, genres:["Hài","Chính kịch"], netflix:false,
                     overview:"Một gia đình lập dị cùng nhau lái xe đưa cô con gái nhỏ đến cuộc thi sắc đẹp." }),
    spiritedaway:mk({ id:129, title:"Spirited Away", year:2001, rating:8.5, genres:["Hoạt hình","Gia đình"], netflix:true,
                     overview:"Cô bé Chihiro lạc vào thế giới linh hồn và phải tìm cách cứu cha mẹ mình." }),

    // mood / duo additions
    yourname:   mk({ id:372058, title:"Your Name", year:2016, rating:8.5, genres:["Hoạt hình","Lãng mạn"], netflix:true,
                     overview:"Hai bạn trẻ xa lạ bỗng hoán đổi thân xác và lần tìm nhau qua không gian, thời gian." }),
    coco:       mk({ id:354912, title:"Coco", year:2017, rating:8.2, genres:["Hoạt hình","Gia đình"], netflix:true,
                     overview:"Cậu bé Miguel lạc vào Vùng Đất Người Chết và khám phá bí mật gia đình về âm nhạc." }),
    greenmile:  mk({ id:497, title:"The Green Mile", year:1999, rating:8.5, genres:["Chính kịch","Kỳ ảo"], netflix:false,
                     overview:"Người cai ngục kết thân với một tử tù mang khả năng chữa lành kỳ lạ." }),
    lalaland:   mk({ id:313369, title:"La La Land", year:2016, rating:8.0, genres:["Lãng mạn","Nhạc kịch"], netflix:false,
                     overview:"Một nhạc công jazz và một diễn viên trẻ yêu nhau giữa Los Angeles đầy mộng mơ." }),
    midnight:   mk({ id:59436, title:"Midnight in Paris", year:2011, rating:7.7, genres:["Lãng mạn","Kỳ ảo"], netflix:false,
                     overview:"Một nhà văn dạo bước Paris về đêm và bất ngờ du hành về thời hoàng kim thập niên 1920." }),
    parasite:   mk({ id:496243, title:"Parasite", year:2019, rating:8.5, genres:["Giật gân","Chính kịch"], netflix:false,
                     overview:"Một gia đình nghèo từng bước len lỏi vào cuộc sống của nhà giàu, dẫn tới bi kịch khó lường." }),
    knives:     mk({ id:546554, title:"Knives Out", year:2019, rating:7.9, genres:["Bí ẩn","Hài"], netflix:true,
                     overview:"Một thám tử lập dị điều tra cái chết bí ẩn của tiểu thuyết gia giàu có giữa gia đình đầy toan tính." }),
    spiderverse:mk({ id:324857, title:"Spider-Man: Into the Spider-Verse", year:2018, rating:8.4, genres:["Hoạt hình","Hành động"], netflix:true,
                     overview:"Miles Morales gặp những Người Nhện từ các vũ trụ song song và học cách trở thành anh hùng." }),
    soul:       mk({ id:508442, title:"Soul", year:2020, rating:8.0, genres:["Hoạt hình","Kỳ ảo"], netflix:false,
                     overview:"Một thầy giáo nhạc jazz lạc vào thế giới linh hồn và đi tìm ý nghĩa thật sự của cuộc sống." }),
    whiplash:   mk({ id:244786, title:"Whiplash", year:2014, rating:8.4, genres:["Chính kịch","Âm nhạc"], netflix:false,
                     overview:"Một tay trống trẻ bị đẩy đến giới hạn dưới sự huấn luyện tàn nhẫn của người thầy ám ảnh." }),
  };

  // ---- VN streaming platforms (logo placeholder = colored chip + abbr) ----
  export const PLATFORMS = {
    netflix:    { name:"Netflix",     color:"#E50914", fg:"#fff", abbr:"N" },
    appletv:    { name:"Apple TV",    color:"#e7eaed", fg:"#111", abbr:"" },
    googleplay: { name:"Google Play", color:"#0aa1f0", fg:"#fff", abbr:"GP" },
    max:        { name:"Max",         color:"#4b3bd6", fg:"#fff", abbr:"M" },
    disney:     { name:"Disney+",     color:"#1a3df0", fg:"#fff", abbr:"D+" },
    fptplay:    { name:"FPT Play",    color:"#f5821f", fg:"#fff", abbr:"FPT" },
    galaxy:     { name:"Galaxy Play", color:"#7c3aed", fg:"#fff", abbr:"GP" },
  };

  // ---- scripted reasoning step builders ----
  function R(thought: string, action: string, observe: string): ReasoningStep {
    return { thought, action, observe };
  }

  // ---- canned flows. key matched by keyword; value is a response object ----
  // response: { text, layout:'carousel'|'big'|'compare'|'none', movies:[], reasoning:[steps], kind:'normal'|'refuse'|'error' }
  const FLOWS = [
    {
      match: /giống inception|tương tự inception|như inception/i,
      label: "gợi ý phim giống Inception trên Netflix",
      res: {
        kind: "normal", layout: "carousel",
        text: "<p>Nếu bạn mê <span class='mv-ref'>Inception</span> — mấy cú twist bẻ não, cấu trúc nhiều tầng và phần hình ảnh choáng ngợp — đây là 5 phim cùng &ldquo;tần số&rdquo;. Mình ưu tiên những phim <strong>đang có trên Netflix VN</strong> trước:</p>",
        movies: [M.shutter, M.interstellar, M.matrix, M.arrival, M.prestige, M.tenet],
        reasoning: [
          R("Người dùng muốn phim tương tự Inception, ràng buộc: đang có trên Netflix VN.",
            "tmdb.movie_recommendations(movie_id=27205)", "Trả về 20 phim gợi ý, gồm Interstellar, Shutter Island, The Prestige, Tenet…"),
          R("Cần lọc theo khả dụng trên Netflix VN.",
            "tmdb.watch_providers(region=\"VN\")", "Interstellar, Shutter Island, The Matrix, Arrival có Netflix VN; Tenet & Prestige hiện không."),
          R("Sắp xếp ưu tiên phim trên Netflix, rồi tới độ tương đồng & rating.",
            "rank(by=[netflix, similarity, rating])", "Danh sách cuối: Shutter Island, Interstellar, The Matrix, Arrival, The Prestige, Tenet."),
        ],
      },
    },
    {
      match: /sci-?fi|khoa học viễn tưởng|trending|thịnh hành|xu hướng/i,
      label: "phim Sci-Fi trending tuần này ở VN",
      res: {
        kind: "normal", layout: "carousel",
        text: "<p>Đây là những phim <strong>Khoa học viễn tưởng</strong> đang nổi nhất tuần này ở Việt Nam, theo dữ liệu trending của TMDB:</p>",
        movies: [M.dune2, M.tenet, M.br2049, M.edgeoftom, M.arrival, M.interstellar],
        reasoning: [
          R("Cần phim sci-fi đang trending, khu vực VN, khung thời gian: tuần.",
            "tmdb.trending(media=\"movie\", window=\"week\")", "Trả về 20 phim trending toàn cầu kèm điểm phổ biến."),
          R("Lọc thể loại Khoa học viễn tưởng (genre_id=878) và cân nhắc mức quan tâm tại VN.",
            "filter(genre=878, region=\"VN\")", "Còn lại 6 phim sci-fi nổi bật: Dune 2, Tenet, Blade Runner 2049, Edge of Tomorrow…"),
        ],
      },
    },
    {
      match: /buồn|nhẹ nhàng|chữa lành|thư giãn|feel.?good|vui vẻ|dễ chịu/i,
      label: "phim nhẹ nhàng khi buồn",
      res: {
        kind: "normal", layout: "carousel",
        text: "<p>Những lúc tâm trạng đi xuống thì phim <strong>ấm áp, nhẹ nhàng</strong> là liều thuốc tốt. Mình chọn vài phim dễ xem, kết đẹp, xem xong thấy nhẹ lòng:</p>",
        movies: [M.paddington2, M.amelie, M.chef, M.grandbud, M.littlemiss, M.spiritedaway],
        reasoning: [
          R("Người dùng đang buồn → cần phim feel-good, tông tích cực, tránh nặng nề/bi kịch.",
            "tmdb.discover(genres=[35,10751], mood=\"uplifting\", min_rating=7.2)", "Trả về danh sách phim hài/gia đình điểm cao: Paddington 2, Amélie, Chef…"),
          R("Loại bỏ phim có nội dung u ám dù thuộc thể loại hài.",
            "filter(exclude_tones=[\"bleak\",\"tragedy\"])", "Giữ lại 6 phim chữa lành phù hợp tâm trạng."),
        ],
      },
    },
    {
      match: /so sánh|đối chiếu|compare|hơn|nên xem cái nào/i,
      label: "so sánh Inception và Interstellar",
      res: {
        kind: "normal", layout: "compare",
        text: "<p>Cùng là Christopher Nolan và đều &ldquo;nặng đô&rdquo; về khái niệm, nhưng hai phim này khác nhau rõ. Mình đặt cạnh nhau cho dễ chọn:</p>",
        movies: [M.inception, M.interstellar],
        compareNote: "<p><strong>Chọn sao?</strong> Thích cú twist, nhịp dồn dập và &ldquo;heist&rdquo; trong giấc mơ → <span class='mv-ref'>Inception</span>. Thích cảm xúc, không gian bao la và yếu tố khoa học → <span class='mv-ref'>Interstellar</span>. Cả hai đều có trên Netflix VN.</p>",
        reasoning: [
          R("Người dùng muốn so sánh — cần lấy chi tiết từng phim để đối chiếu.",
            "tmdb.movie_details([27205, 157336])", "Lấy được rating, thể loại, thời lượng, tóm tắt của cả hai phim."),
          R("Trích các trục so sánh: tông phim, nhịp, độ phức tạp, khả dụng.",
            "build_comparison(axes=[tone, pace, theme, availability])", "Lập bảng đối chiếu hai phim hoàn tất."),
        ],
      },
    },
    {
      match: /có trên netflix|netflix vn không|xem ở đâu|coi ở đâu|đang chiếu ở đâu|available/i,
      label: "Dune: Part Two có trên Netflix VN không?",
      res: {
        kind: "normal", layout: "big",
        text: "<p>Mình kiểm tra dữ liệu nhà cung cấp của TMDB cho khu vực <strong>Việt Nam</strong>:</p>",
        movies: [M.dune2],
        availability: {
          netflix: false,
          where: { flatrate: [], rent: ["appletv","googleplay","fptplay"], buy: ["appletv","googleplay"], soon: ["max"] },
          note: "<strong>Chưa có trên Netflix VN.</strong> Hiện bạn có thể thuê hoặc mua trên các nền tảng dưới đây; nhiều khả năng sẽ lên Max trong thời gian tới.",
        },
        reasoning: [
          R("Xác định phim người dùng hỏi và kiểm tra provider tại VN.",
            "tmdb.search_movie(\"Dune Part Two\")", "Khớp Dune: Part Two (2024), id=693134."),
          R("Tra cứu nhà cung cấp theo khu vực VN.",
            "tmdb.watch_providers(693134, region=\"VN\")", "flatrate: []; rent/buy: [Apple TV, Google Play]. Không có Netflix."),
        ],
      },
    },
  ];

  // off-topic refusal
  export const REFUSE: ChatResponse = {
    kind: "refuse", layout: "none",
    text: "<p>Mình là trợ lý <strong>gợi ý phim</strong> nên câu này hơi ngoài chuyên môn của mình rồi. Mình chưa trả lời được về chủ đề đó, nhưng rất sẵn lòng giúp bạn tìm phim!</p><p>Thử hỏi mình kiểu:</p>",
    refuseChips: [
      "Gợi ý phim hành động hay 2024",
      "Phim kinh dị nhẹ đô cho người yếu tim",
      "Có gì hay trên Netflix VN tuần này?",
    ],
  };

  // generic fallback for any other movie-ish query
  export const FALLBACK: ChatResponse = {
    kind: "normal", layout: "carousel",
    text: "<p>Dựa trên yêu cầu của bạn, đây là vài gợi ý mình thấy hợp nhất. Bạn nói rõ thêm về <strong>thể loại, tâm trạng hoặc nền tảng</strong> thì mình lọc chính xác hơn nhé:</p>",
    movies: [M.dune2, M.interstellar, M.prestige, M.arrival, M.grandbud, M.matrix],
    reasoning: [
      R("Yêu cầu khá mở → suy luận theo các phim chất lượng cao, đa dạng thể loại.",
        "tmdb.discover(sort_by=\"vote_average.desc\", vote_count.gte=2000)", "Trả về danh sách phim rating cao nhiều thể loại."),
      R("Chọn lọc để vừa đa dạng vừa dễ tiếp cận khán giả VN.",
        "diversify(by=\"genre\", limit=6)", "Chốt 6 phim làm gợi ý khởi đầu."),
    ],
  };

  // ---- Moods (visual picker on empty state) ----
  function R2(thought: string, action: string, observe: string): ReasoningStep {
    return { thought, action, observe };
  }
  export const MOODS = [
    { id:"cry", label:"Cần khóc một trận", sub:"Phim lấy nước mắt", icon:"tear", h:212,
      prompt:"Mình đang muốn xem một phim thật cảm động, khóc được một trận cho nhẹ lòng.",
      movies:[M.greenmile, M.coco, M.yourname, M.interstellar, M.soul, M.whiplash] },
    { id:"laugh", label:"Cười xả stress", sub:"Hài, nhẹ đầu", icon:"smile", h:38,
      prompt:"Cho mình vài phim hài nhẹ nhàng để cười xả stress với.",
      movies:[M.grandbud, M.knives, M.chef, M.paddington2, M.littlemiss, M.midnight] },
    { id:"tense", label:"Nín thở tới phút cuối", sub:"Giật gân, hồi hộp", icon:"pulse", h:352,
      prompt:"Mình muốn một phim căng thẳng, hồi hộp nín thở từ đầu tới cuối.",
      movies:[M.parasite, M.shutter, M.prestige, M.tenet, M.br2049, M.inception] },
    { id:"date", label:"Tối hẹn hò", sub:"Lãng mạn, ấm áp", icon:"heart", h:332,
      prompt:"Gợi ý phim lãng mạn hợp xem tối hẹn hò.",
      movies:[M.lalaland, M.amelie, M.yourname, M.midnight, M.coco, M.grandbud] },
    { id:"bg", label:"Xem nền khi làm việc", sub:"Dễ xem, không cần tập trung", icon:"monitor", h:198,
      prompt:"Mình cần phim dễ xem, mở nền khi làm việc cũng được, không phải nghĩ nhiều.",
      movies:[M.paddington2, M.chef, M.spiderverse, M.knives, M.grandbud, M.midnight] },
    { id:"heal", label:"Chữa lành nhẹ nhàng", sub:"Ấm áp, an yên", icon:"leaf", h:148,
      prompt:"Cho mình phim chữa lành, nhẹ nhàng an yên để xem cuối tuần.",
      movies:[M.soul, M.spiritedaway, M.coco, M.amelie, M.chef, M.paddington2] },
  ];
  export function moodRes(m: (typeof MOODS)[number]): ChatResponse {
    return {
      kind:"normal", layout:"carousel",
      text:`<p>Hợp với tâm trạng <strong>“${m.label.toLowerCase()}”</strong> rồi. Mình chọn ${m.movies.length} phim đúng &ldquo;gu&rdquo; đó, ưu tiên phim dễ tiếp cận ở VN:</p>`,
      movies:m.movies,
      reasoning:[
        R2(`Người dùng chọn tâm trạng: ${m.label}. Cần phim đúng tông cảm xúc này.`,
          `tmdb.discover(mood="${m.id}", region="VN")`, "Trả về danh sách phim phù hợp tông cảm xúc, đã lọc theo điểm số."),
        R2("Sắp xếp ưu tiên phim có nền tảng tại VN và rating cao.",
          "rank(by=[availability_vn, rating])", `Chốt ${m.movies.length} phim cho gợi ý.`),
      ],
    };
  }

  // ---- "Đôi mình xem gì?" — intersection of two tastes ----
  export function buildDuo(a: string, b: string): ChatResponse {
    const ta = (a||"").trim() || "gu A", tb = (b||"").trim() || "gu B";
    const picks = [
      { m:M.parasite,   why:`Căng và sâu cho người mê <em>${ta}</em>, nhưng tình huống trớ trêu lại rất hợp người thích <em>${tb}</em>.` },
      { m:M.knives,     why:`Bí ẩn gay cấn pha hài duyên — điểm chạm dễ chịu giữa <em>${ta}</em> và <em>${tb}</em>.` },
      { m:M.spiderverse,why:`Hành động mãn nhãn nhưng cảm xúc và hài hước đủ đầy, hiếm ai trong hai người thấy chán.` },
      { m:M.grandbud,   why:`Phong cách độc đáo, vừa lạ vừa vui — an toàn cho cả hai gu khác nhau.` },
    ];
    return {
      kind:"normal", layout:"duo", tasteA:ta, tasteB:tb,
      text:`<p>Một người thích <span class='mv-ref'>${ta}</span>, một người thích <span class='mv-ref'>${tb}</span> — mình tìm <strong>điểm giao</strong> để cả hai cùng vui. 4 phim &ldquo;trung lập&rdquo; nhất:</p>`,
      duoPicks:picks,
      reasoning:[
        R2(`Hai gu khác nhau: "${ta}" và "${tb}". Cần tìm phim nằm ở vùng giao.`,
          `tmdb.discover(genres_any=[A,B], sort="vote_average")`, "Lấy các phim chạm được nhiều thể loại, điểm cao."),
        R2("Loại phim quá thiên về một phía; ưu tiên phim đa tầng, dễ đồng thuận.",
          "rank(by=[cross_appeal, rating])", "Chốt 4 phim cân bằng nhất cho cả hai."),
      ],
    };
  }

  // off-topic detector: queries clearly not about movies
  export const OFFTOPIC = /thời tiết|tỷ giá|chứng khoán|bitcoin|nấu ăn|công thức|code|lập trình|toán|bài tập|chính trị|bầu cử|sức khỏe|bệnh|thuốc|tin tức|bóng đá|thể thao(?! phim)/i;

  // demo trigger for the API-error state (no settings toggle anymore)
  const ERRWORD = /demo lỗi|test lỗi|lỗi api|mô phỏng lỗi|simulate error/i;

  // resolve a user message -> response object (sample mode)
  export function resolveResponse(text: string): ChatResponse {
    if (ERRWORD.test(text)) {
      return { kind:"error", layout:"none",
        text:"Không kết nối được tới máy chủ agent (POST /api/chat). Có thể backend chưa chạy hoặc đã hết thời gian chờ.",
        errCode:"ECONNREFUSED · timeout sau 30s" };
    }
    if (OFFTOPIC.test(text)) return REFUSE;
    for (const f of FLOWS) { if (f.match.test(text)) return f.res as ChatResponse; }
    return FALLBACK;
  };

  // suggestion chips (empty state)
  export const SUGGESTIONS: { icon: string; text: string }[] = [
    { icon:"layers", text:"Gợi ý phim giống Inception trên Netflix" },
    { icon:"trending", text:"Phim Sci-Fi trending tuần này ở VN" },
    { icon:"heart", text:"Phim nhẹ nhàng để xem khi buồn" },
    { icon:"compare", text:"So sánh Inception và Interstellar" },
    { icon:"check", text:"Dune: Part Two có trên Netflix VN không?" },
  ];