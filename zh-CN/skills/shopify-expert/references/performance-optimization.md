# 性能优化

---

## 使用场景

- 提升 Shopify 店铺速度评分
- 优化核心网页指标（LCP、FID、CLS）
- 减少页面加载时间
- 优化图片和资源
- 实现懒加载策略
- 分析和修复性能瓶颈

## 不适用场景

- 结账流程性能（主要由 Shopify 控制）
- 服务器端 API 优化（使用 Admin API 最佳实践）
- 无头商店性能（使用 Hydrogen/框架特定模式）

---

## 性能指标概览

### 目标基准

| 指标 | 良好 | 需要改进 | 较差 |
|------|------|----------|------|
| LCP（最大内容绘制） | < 2.5s | 2.5s - 4s | > 4s |
| FID（首次输入延迟） | < 100ms | 100ms - 300ms | > 300ms |
| CLS（累积布局偏移） | < 0.1 | 0.1 - 0.25 | > 0.25 |
| TTFB（首字节时间） | < 600ms | 600ms - 1800ms | > 1800ms |
| 速度指数 | < 3.4s | 3.4s - 5.8s | > 5.8s |

### 性能测量

```bash
# Shopify Theme Inspector Chrome Extension
# Install from Chrome Web Store

# Lighthouse CI
npm install -g @lhci/cli
lhci autorun --collect.url=https://your-store.myshopify.com

# Web Vitals JavaScript
npm install web-vitals
```

```javascript
// Track Core Web Vitals
import { onCLS, onFID, onLCP, onTTFB, onINP } from 'web-vitals';

function sendToAnalytics({ name, delta, id }) {
  // Send to your analytics service
  gtag('event', name, {
    event_category: 'Web Vitals',
    event_label: id,
    value: Math.round(name === 'CLS' ? delta * 1000 : delta),
    non_interaction: true,
  });
}

onCLS(sendToAnalytics);
onFID(sendToAnalytics);
onLCP(sendToAnalytics);
onTTFB(sendToAnalytics);
onINP(sendToAnalytics); // Replaces FID in 2024
```

---

## 图片优化

### 使用 Shopify CDN 的响应式图片

```liquid
{% comment %} Modern responsive image pattern {% endcomment %}
{% liquid
  assign image = product.featured_image
  assign image_widths = '180, 360, 540, 720, 900, 1080, 1296, 1512, 1728, 1944, 2160'
%}

<img
  srcset="
    {%- for width in image_widths -%}
      {{ image | image_url: width: width }} {{ width }}w{% unless forloop.last %}, {% endunless %}
    {%- endfor -%}
  "
  sizes="(min-width: 1200px) 50vw, (min-width: 768px) 75vw, 100vw"
  src="{{ image | image_url: width: 720 }}"
  alt="{{ image.alt | escape }}"
  width="{{ image.width }}"
  height="{{ image.height }}"
  loading="lazy"
  decoding="async"
>

{% comment %} For hero/above-the-fold images - no lazy loading {% endcomment %}
<img
  srcset="{{ image | image_url: width: 1080 }} 1080w,
          {{ image | image_url: width: 1920 }} 1920w,
          {{ image | image_url: width: 2560 }} 2560w"
  sizes="100vw"
  src="{{ image | image_url: width: 1920 }}"
  alt="{{ image.alt | escape }}"
  width="{{ image.width }}"
  height="{{ image.height }}"
  loading="eager"
  fetchpriority="high"
  decoding="sync"
>
```

### 用于视觉方向的 Picture 元素

```liquid
{% comment %} Different crops for mobile vs desktop {% endcomment %}
<picture>
  <source
    media="(max-width: 749px)"
    srcset="{{ section.settings.mobile_image | image_url: width: 750 }}"
  >
  <source
    media="(min-width: 750px)"
    srcset="{{ section.settings.desktop_image | image_url: width: 1500 }} 1x,
            {{ section.settings.desktop_image | image_url: width: 3000 }} 2x"
  >
  <img
    src="{{ section.settings.desktop_image | image_url: width: 1500 }}"
    alt="{{ section.settings.desktop_image.alt | escape }}"
    width="1500"
    height="600"
    loading="lazy"
  >
</picture>
```

### 使用 CSS 的背景图片

```liquid
{% comment %} Background images should still use srcset pattern {% endcomment %}
{% style %}
  .hero-banner {
    background-image: url('{{ section.settings.image | image_url: width: 750 }}');
  }

  @media screen and (min-width: 750px) {
    .hero-banner {
      background-image: url('{{ section.settings.image | image_url: width: 1500 }}');
    }
  }

  @media screen and (min-width: 1200px) {
    .hero-banner {
      background-image: url('{{ section.settings.image | image_url: width: 2000 }}');
    }
  }
{% endstyle %}
```

---

## JavaScript 优化

### 推迟非关键 JavaScript

```liquid
{% comment %} layout/theme.liquid {% endcomment %}

{% comment %} Critical JS - loaded sync {% endcomment %}
<script src="{{ 'critical.js' | asset_url }}"></script>

{% comment %} Non-critical JS - deferred {% endcomment %}
<script src="{{ 'theme.js' | asset_url }}" defer></script>
<script src="{{ 'cart.js' | asset_url }}" defer></script>

{% comment %} Third-party scripts - load after page {% endcomment %}
<script>
  window.addEventListener('load', function() {
    // Load analytics, chat widgets, etc.
    var script = document.createElement('script');
    script.src = 'https://third-party.com/widget.js';
    script.async = true;
    document.body.appendChild(script);
  });
</script>
```

### 用于代码分割的模块模式

```javascript
// assets/product.js
const ProductForm = {
  init() {
    const form = document.querySelector('[data-product-form]');
    if (!form) return;

    this.form = form;
    this.bindEvents();
  },

  bindEvents() {
    this.form.addEventListener('submit', this.handleSubmit.bind(this));
  },

  async handleSubmit(e) {
    e.preventDefault();

    // Lazy load cart functionality when needed
    const { Cart } = await import('./cart.js');
    Cart.add(new FormData(this.form));
  }
};

document.addEventListener('DOMContentLoaded', () => ProductForm.init());
```

### 用于懒加载的 Intersection Observer

```javascript
// assets/lazy-load.js
const lazyLoad = {
  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(this.handleIntersect.bind(this), {
        rootMargin: '200px 0px', // Load 200px before viewport
        threshold: 0.01
      });

      document.querySelectorAll('[data-lazy]').forEach(el => {
        this.observer.observe(el);
      });
    } else {
      // Fallback for older browsers
      this.loadAll();
    }
  },

  handleIntersect(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        this.load(entry.target);
        this.observer.unobserve(entry.target);
      }
    });
  },

  load(element) {
    const type = element.dataset.lazy;

    switch (type) {
      case 'image':
        element.src = element.dataset.src;
        if (element.dataset.srcset) {
          element.srcset = element.dataset.srcset;
        }
        break;

      case 'section':
        this.loadSection(element);
        break;

      case 'video':
        element.src = element.dataset.src;
        break;
    }

    element.removeAttribute('data-lazy');
  },

  async loadSection(element) {
    const url = element.dataset.url;
    const response = await fetch(url);
    const html = await response.text();
    element.innerHTML = html;
  },

  loadAll() {
    document.querySelectorAll('[data-lazy]').forEach(el => this.load(el));
  }
};

document.addEventListener('DOMContentLoaded', () => lazyLoad.init());
```

---

## CSS 优化

### 关键 CSS 提取

```liquid
{% comment %} layout/theme.liquid {% endcomment %}
<head>
  {% comment %} Inline critical CSS {% endcomment %}
  <style>
    {% render 'critical-css' %}
  </style>

  {% comment %} Preload full stylesheet {% endcomment %}
  <link rel="preload" href="{{ 'theme.css' | asset_url }}" as="style">

  {% comment %} Load full stylesheet with low priority {% endcomment %}
  <link
    rel="stylesheet"
    href="{{ 'theme.css' | asset_url }}"
    media="print"
    onload="this.media='all'"
  >
  <noscript>
    <link rel="stylesheet" href="{{ 'theme.css' | asset_url }}">
  </noscript>
</head>
```

```liquid
{% comment %} snippets/critical-css.liquid {% endcomment %}
/* Reset and base styles */
*,*::before,*::after{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,sans-serif;line-height:1.5}
img{max-width:100%;height:auto;display:block}

/* Header layout */
.header{position:sticky;top:0;z-index:100;background:#fff}
.header__wrapper{display:flex;align-items:center;justify-content:space-between;padding:1rem}

/* Hero section */
.hero{position:relative;min-height:50vh;display:flex;align-items:center}
.hero__content{max-width:600px;padding:2rem}

/* Product grid skeleton */
.product-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:1rem}
.product-card{aspect-ratio:1}
```

### 防止布局偏移

```liquid
{% comment %} Always define dimensions {% endcomment %}
<img
  src="{{ image | image_url: width: 400 }}"
  width="{{ image.width }}"
  height="{{ image.height }}"
  alt="{{ image.alt | escape }}"
  loading="lazy"
>

{% comment %} Use aspect-ratio CSS {% endcomment %}
<style>
  .product-card__image {
    aspect-ratio: 1 / 1;
    object-fit: cover;
    width: 100%;
    height: auto;
  }

  .hero__image {
    aspect-ratio: 16 / 9;
    object-fit: cover;
  }
</style>

{% comment %} Reserve space for dynamic content {% endcomment %}
<div class="reviews-container" style="min-height: 200px;">
  {% comment %} Reviews loaded via JS {% endcomment %}
</div>
```

### 字体优化

```liquid
{% comment %} layout/theme.liquid head section {% endcomment %}

{% comment %} Preconnect to font providers {% endcomment %}
<link rel="preconnect" href="https://fonts.shopifycdn.com" crossorigin>

{% comment %} Preload critical fonts {% endcomment %}
{% if settings.type_header_font.system? == false %}
  <link
    rel="preload"
    href="{{ settings.type_header_font | font_url }}"
    as="font"
    type="font/woff2"
    crossorigin
  >
{% endif %}

{% comment %} Use font-display: swap {% endcomment %}
<style>
  {{ settings.type_header_font | font_face: font_display: 'swap' }}
  {{ settings.type_body_font | font_face: font_display: 'swap' }}
</style>

{% comment %} System font stack fallback {% endcomment %}
<style>
  :root {
    --font-body: {{ settings.type_body_font.family }}, {{ settings.type_body_font.fallback_families }};
    --font-heading: {{ settings.type_header_font.family }}, {{ settings.type_header_font.fallback_families }};
  }

  body {
    font-family: var(--font-body);
  }

  h1, h2, h3 {
    font-family: var(--font-heading);
  }
</style>
```

---

## 资源加载策略

### 预加载关键资源

```liquid
{% comment %} layout/theme.liquid head {% endcomment %}

{% comment %} DNS prefetch for third-party domains {% endcomment %}
<link rel="dns-prefetch" href="https://cdn.shopify.com">
<link rel="dns-prefetch" href="https://www.googletagmanager.com">

{% comment %} Preconnect for critical third-parties {% endcomment %}
<link rel="preconnect" href="https://cdn.shopify.com" crossorigin>

{% comment %} Preload hero image (above the fold) {% endcomment %}
{% if template == 'index' %}
  {% assign hero_image = sections['hero'].settings.image %}
  {% if hero_image %}
    <link
      rel="preload"
      as="image"
      href="{{ hero_image | image_url: width: 1500 }}"
      imagesrcset="{{ hero_image | image_url: width: 750 }} 750w,
                   {{ hero_image | image_url: width: 1500 }} 1500w,
                   {{ hero_image | image_url: width: 3000 }} 3000w"
      imagesizes="100vw"
    >
  {% endif %}
{% endif %}

{% comment %} Preload critical scripts {% endcomment %}
<link rel="modulepreload" href="{{ 'theme.js' | asset_url }}">
```

### 懒加载区块

```liquid
{% comment %} templates/index.json - defer below-the-fold sections {% endcomment %}

{% comment %} In section file {% endcomment %}
{% if section.index > 3 %}
  <div
    class="lazy-section"
    data-section-url="{{ section.id | prepend: '?section_id=' | prepend: request.path }}"
    data-lazy="section"
  >
    <div class="section-placeholder" style="min-height: 400px;">
      {% comment %} Loading skeleton {% endcomment %}
      <div class="skeleton-loader"></div>
    </div>
  </div>
{% else %}
  {% comment %} Render normally for above-the-fold {% endcomment %}
  {% render 'section-content' %}
{% endif %}
```

```javascript
// assets/lazy-sections.js
document.addEventListener('DOMContentLoaded', () => {
  const lazySections = document.querySelectorAll('[data-lazy="section"]');

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(async (entry) => {
        if (entry.isIntersecting) {
          const section = entry.target;
          const url = section.dataset.sectionUrl;

          try {
            const response = await fetch(url);
            const html = await response.text();
            section.innerHTML = html;
            section.removeAttribute('data-lazy');
          } catch (error) {
            console.error('Failed to load section:', error);
          }

          observer.unobserve(section);
        }
      });
    }, { rootMargin: '400px' });

    lazySections.forEach(section => observer.observe(section));
  }
});
```

---

## 缓存策略

### 浏览器缓存头

```liquid
{% comment %} Shopify handles most caching automatically {% endcomment %}
{% comment %} For custom apps, set proper headers {% endcomment %}
```

```typescript
// For Hydrogen/custom storefronts
export async function loader({ context }: LoaderFunctionArgs) {
  const { storefront } = context;

  // Cache product data for 1 hour
  const products = await storefront.query(PRODUCTS_QUERY, {
    cache: storefront.CacheLong(), // ~1 hour
  });

  // Short cache for inventory
  const inventory = await storefront.query(INVENTORY_QUERY, {
    cache: storefront.CacheShort(), // ~1 minute
  });

  return json({ products, inventory }, {
    headers: {
      'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
    },
  });
}
```

### 本地存储缓存

```javascript
// assets/cache.js
const Cache = {
  prefix: 'shopify_',
  ttl: 5 * 60 * 1000, // 5 minutes

  set(key, value, customTtl) {
    const item = {
      value,
      expiry: Date.now() + (customTtl || this.ttl),
    };
    try {
      localStorage.setItem(this.prefix + key, JSON.stringify(item));
    } catch (e) {
      // Handle quota exceeded
      this.cleanup();
    }
  },

  get(key) {
    try {
      const item = JSON.parse(localStorage.getItem(this.prefix + key));
      if (!item) return null;
      if (Date.now() > item.expiry) {
        localStorage.removeItem(this.prefix + key);
        return null;
      }
      return item.value;
    } catch (e) {
      return null;
    }
  },

  cleanup() {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(this.prefix));
    keys.forEach(key => {
      try {
        const item = JSON.parse(localStorage.getItem(key));
        if (Date.now() > item.expiry) {
          localStorage.removeItem(key);
        }
      } catch (e) {
        localStorage.removeItem(key);
      }
    });
  }
};

// Usage: Cache product recommendations
async function getRecommendations(productId) {
  const cacheKey = `recommendations_${productId}`;
  const cached = Cache.get(cacheKey);

  if (cached) return cached;

  const response = await fetch(`/recommendations/products.json?product_id=${productId}&limit=4`);
  const data = await response.json();

  Cache.set(cacheKey, data.products);
  return data.products;
}
```

---

## 第三方脚本管理

### 脚本加载策略

```liquid
{% comment %} snippets/third-party-scripts.liquid {% endcomment %}

{% comment %} Load after user interaction {% endcomment %}
<script>
  (function() {
    var loaded = false;

    function loadScripts() {
      if (loaded) return;
      loaded = true;

      // Google Analytics
      var ga = document.createElement('script');
      ga.src = 'https://www.googletagmanager.com/gtag/js?id={{ settings.ga_id }}';
      ga.async = true;
      document.body.appendChild(ga);

      // Chat widget
      {% if settings.enable_chat %}
        var chat = document.createElement('script');
        chat.src = '{{ settings.chat_script_url }}';
        chat.async = true;
        document.body.appendChild(chat);
      {% endif %}

      // Reviews widget
      {% if settings.enable_reviews %}
        setTimeout(function() {
          var reviews = document.createElement('script');
          reviews.src = '{{ settings.reviews_script_url }}';
          reviews.async = true;
          document.body.appendChild(reviews);
        }, 2000); // Delay reviews by 2 seconds
      {% endif %}
    }

    // Load on user interaction
    ['mousedown', 'mousemove', 'touchstart', 'scroll', 'keydown'].forEach(function(event) {
      window.addEventListener(event, loadScripts, { once: true, passive: true });
    });

    // Fallback: load after 5 seconds
    setTimeout(loadScripts, 5000);
  })();
</script>
```

### 用于第三方脚本的 Partytown

```html
<!-- Move third-party scripts to web worker -->
<script>
  partytown = {
    forward: ['dataLayer.push', 'fbq'],
  };
</script>
<script src="/~partytown/partytown.js"></script>

<!-- Scripts run in worker -->
<script type="text/partytown">
  // Google Analytics runs in web worker
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

---

## 性能检查清单

### 上线前审核

```markdown
## Images
- [ ] All images use responsive srcset
- [ ] Above-fold images have fetchpriority="high"
- [ ] Below-fold images have loading="lazy"
- [ ] All images have width/height attributes
- [ ] WebP format used where supported

## JavaScript
- [ ] Non-critical JS is deferred
- [ ] Third-party scripts load on interaction
- [ ] No render-blocking scripts
- [ ] Code splitting for large modules
- [ ] Console errors resolved

## CSS
- [ ] Critical CSS inlined
- [ ] Non-critical CSS loaded async
- [ ] No unused CSS in critical path
- [ ] Font-display: swap for all fonts
- [ ] No layout shift from fonts

## Resources
- [ ] Preconnect to critical origins
- [ ] Preload critical assets
- [ ] DNS prefetch for third parties
- [ ] HTTP/2 server push configured

## Metrics
- [ ] LCP < 2.5s on mobile
- [ ] FID < 100ms
- [ ] CLS < 0.1
- [ ] Speed Index < 3.4s
- [ ] Total page weight < 2MB
```

---

## 相关参考

- **Liquid 模板** - 用于主题级别的优化
- **Storefront API** - 用于无头商店性能模式
- **结账自定义** - 结账扩展性能