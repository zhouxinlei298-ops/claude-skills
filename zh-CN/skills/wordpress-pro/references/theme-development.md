# 主题开发

---

## 模板层级

WordPress 使用特定的层级来确定哪个模板文件渲染内容。理解这个层级对于主题开发至关重要。

### 层级顺序（从最具体到一般）

```
1. Custom Template (page-{custom}.php)
2. Specific Template (single-{post-type}-{slug}.php)
3. Type Template (single-{post-type}.php)
4. Archive Template (archive-{post-type}.php)
5. General Template (single.php, archive.php)
6. Index Fallback (index.php)
```

### 完整模板映射

```php
<?php
/**
 * Template hierarchy reference for WordPress 6.4+
 *
 * Homepage:
 *   front-page.php → home.php → index.php
 *
 * Single Post:
 *   single-{post-type}-{slug}.php → single-{post-type}.php → single.php → singular.php → index.php
 *
 * Page:
 *   {custom-template}.php → page-{slug}.php → page-{id}.php → page.php → singular.php → index.php
 *
 * Category:
 *   category-{slug}.php → category-{id}.php → category.php → archive.php → index.php
 *
 * Custom Taxonomy:
 *   taxonomy-{taxonomy}-{term}.php → taxonomy-{taxonomy}.php → taxonomy.php → archive.php → index.php
 *
 * Custom Post Type Archive:
 *   archive-{post-type}.php → archive.php → index.php
 *
 * Author:
 *   author-{nicename}.php → author-{id}.php → author.php → archive.php → index.php
 *
 * Date:
 *   date.php → archive.php → index.php
 *
 * Search:
 *   search.php → index.php
 *
 * 404:
 *   404.php → index.php
 *
 * Attachment:
 *   {mime-type}.php → attachment.php → single-attachment-{slug}.php → single.php → singular.php → index.php
 */
```

---

## 传统主题结构

### 最小主题要求

```
theme-name/
├── style.css          # Required: Theme metadata
├── index.php          # Required: Main template fallback
├── functions.php      # Theme setup and functionality
├── header.php         # Site header
├── footer.php         # Site footer
├── sidebar.php        # Widget area
├── single.php         # Single post template
├── page.php           # Page template
├── archive.php        # Archive template
├── search.php         # Search results
├── 404.php            # Not found page
├── comments.php       # Comment template
├── screenshot.png     # Theme preview (1200x900)
└── assets/
    ├── css/
    ├── js/
    └── images/
```

### style.css 头部

```css
/*
Theme Name: Theme Name
Theme URI: https://example.com/theme
Author: Author Name
Author URI: https://example.com
Description: A custom WordPress theme with modern features.
Version: 1.0.0
Requires at least: 6.4
Tested up to: 6.5
Requires PHP: 8.1
License: GNU General Public License v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: theme-name
Tags: custom-background, custom-logo, custom-menu, featured-images, threaded-comments
*/
```

### functions.php 设置

```php
<?php
declare(strict_types=1);

/**
 * Theme functions and definitions
 *
 * @package Theme_Name
 * @since 1.0.0
 */

namespace ThemeName;

// Prevent direct access
defined('ABSPATH') || exit;

/**
 * Theme setup
 */
function theme_setup(): void {
    // Make theme translation-ready
    load_theme_textdomain('theme-name', get_template_directory() . '/languages');

    // Add default posts and comments RSS feed links
    add_theme_support('automatic-feed-links');

    // Let WordPress manage the document title
    add_theme_support('title-tag');

    // Enable featured images
    add_theme_support('post-thumbnails');
    add_image_size('theme-featured', 1200, 630, true);
    add_image_size('theme-card', 600, 400, true);

    // Register navigation menus
    register_nav_menus([
        'primary'   => esc_html__('Primary Menu', 'theme-name'),
        'footer'    => esc_html__('Footer Menu', 'theme-name'),
        'mobile'    => esc_html__('Mobile Menu', 'theme-name'),
    ]);

    // Switch to HTML5 markup
    add_theme_support('html5', [
        'search-form',
        'comment-form',
        'comment-list',
        'gallery',
        'caption',
        'style',
        'script',
        'navigation-widgets',
    ]);

    // Enable selective refresh for widgets
    add_theme_support('customize-selective-refresh-widgets');

    // Add custom logo support
    add_theme_support('custom-logo', [
        'height'      => 100,
        'width'       => 400,
        'flex-height' => true,
        'flex-width'  => true,
    ]);

    // Add responsive embed support
    add_theme_support('responsive-embeds');

    // Add editor styles
    add_theme_support('editor-styles');
    add_editor_style('assets/css/editor-style.css');

    // Wide and full alignment support
    add_theme_support('align-wide');

    // Block styles
    add_theme_support('wp-block-styles');
}
add_action('after_setup_theme', __NAMESPACE__ . '\\theme_setup');

/**
 * Enqueue scripts and styles
 */
function enqueue_assets(): void {
    $theme_version = wp_get_theme()->get('Version');
    $assets_path = get_template_directory() . '/assets';
    $assets_uri = get_template_directory_uri() . '/assets';

    // Main stylesheet
    wp_enqueue_style(
        'theme-name-style',
        $assets_uri . '/css/main.css',
        [],
        filemtime($assets_path . '/css/main.css')
    );

    // Main JavaScript
    wp_enqueue_script(
        'theme-name-script',
        $assets_uri . '/js/main.js',
        [],
        filemtime($assets_path . '/js/main.js'),
        true
    );

    // Localize script with data
    wp_localize_script('theme-name-script', 'themeNameData', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'nonce'   => wp_create_nonce('theme_name_nonce'),
        'homeUrl' => home_url('/'),
    ]);

    // Comment reply script
    if (is_singular() && comments_open() && get_option('thread_comments')) {
        wp_enqueue_script('comment-reply');
    }
}
add_action('wp_enqueue_scripts', __NAMESPACE__ . '\\enqueue_assets');

/**
 * Register widget areas
 */
function register_sidebars(): void {
    register_sidebar([
        'name'          => esc_html__('Main Sidebar', 'theme-name'),
        'id'            => 'sidebar-main',
        'description'   => esc_html__('Add widgets here.', 'theme-name'),
        'before_widget' => '<section id="%1$s" class="widget %2$s">',
        'after_widget'  => '</section>',
        'before_title'  => '<h3 class="widget-title">',
        'after_title'   => '</h3>',
    ]);

    register_sidebar([
        'name'          => esc_html__('Footer Widgets', 'theme-name'),
        'id'            => 'sidebar-footer',
        'description'   => esc_html__('Footer widget area.', 'theme-name'),
        'before_widget' => '<div id="%1$s" class="widget %2$s">',
        'after_widget'  => '</div>',
        'before_title'  => '<h4 class="widget-title">',
        'after_title'   => '</h4>',
    ]);
}
add_action('widgets_init', __NAMESPACE__ . '\\register_sidebars');

/**
 * Set content width
 */
function set_content_width(): void {
    $GLOBALS['content_width'] = apply_filters('theme_name_content_width', 1200);
}
add_action('after_setup_theme', __NAMESPACE__ . '\\set_content_width', 0);
```

---

## 子主题开发

### 何时使用子主题

**使用子主题时：**
- 定位现有主题
- 对父主题进行 CSS 修改
- 覆盖特定模板文件
- 添加功能而不修改父主题

**使用自定义主题时：**
- 从零开始构建
- 需要重大结构更改
- 不同的设计系统要求

### 子主题结构

```
theme-name-child/
├── style.css          # Required: Child theme metadata
├── functions.php      # Child theme functions
├── screenshot.png     # Child theme preview
└── templates/         # Template overrides
    └── parts/
```

### 子主题 style.css

```css
/*
Theme Name: Theme Name Child
Theme URI: https://example.com/theme-child
Description: Child theme for Theme Name
Author: Author Name
Author URI: https://example.com
Template: theme-name
Version: 1.0.0
Requires at least: 6.4
Tested up to: 6.5
Requires PHP: 8.1
License: GNU General Public License v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Text Domain: theme-name-child
*/

/* Child theme styles below */
```

### 子主题 functions.php

```php
<?php
declare(strict_types=1);

/**
 * Child theme functions
 *
 * @package Theme_Name_Child
 */

namespace ThemeNameChild;

defined('ABSPATH') || exit;

/**
 * Enqueue parent and child theme styles
 */
function enqueue_styles(): void {
    $parent_style = 'theme-name-style';

    // Enqueue parent theme stylesheet
    wp_enqueue_style(
        $parent_style,
        get_template_directory_uri() . '/assets/css/main.css',
        [],
        wp_get_theme()->parent()->get('Version')
    );

    // Enqueue child theme stylesheet
    wp_enqueue_style(
        'theme-name-child-style',
        get_stylesheet_uri(),
        [$parent_style],
        wp_get_theme()->get('Version')
    );
}
add_action('wp_enqueue_scripts', __NAMESPACE__ . '\\enqueue_styles');

/**
 * Override parent theme functions as needed
 */
```

---

## 块主题开发（FSE）

WordPress 6.4+ 完全支持使用块主题的全站编辑（Full Site Editing）。

### 块主题结构

```
block-theme/
├── style.css              # Theme metadata
├── theme.json             # Global settings and styles
├── functions.php          # Theme functions (minimal for block themes)
├── templates/             # Block templates (HTML)
│   ├── index.html         # Required: Main fallback
│   ├── front-page.html    # Homepage
│   ├── single.html        # Single posts
│   ├── page.html          # Pages
│   ├── archive.html       # Archives
│   ├── search.html        # Search results
│   └── 404.html           # Not found
├── parts/                 # Template parts
│   ├── header.html
│   ├── footer.html
│   └── sidebar.html
├── patterns/              # Block patterns
│   └── hero-section.php
└── assets/
    ├── fonts/
    └── images/
```

### theme.json（WordPress 6.4+）

```json
{
    "$schema": "https://schemas.wp.org/trunk/theme.json",
    "version": 3,
    "settings": {
        "appearanceTools": true,
        "useRootPaddingAwareAlignments": true,
        "layout": {
            "contentSize": "800px",
            "wideSize": "1200px"
        },
        "color": {
            "defaultDuotone": false,
            "defaultGradients": false,
            "defaultPalette": false,
            "palette": [
                {
                    "color": "#1a1a2e",
                    "name": "Primary",
                    "slug": "primary"
                },
                {
                    "color": "#16213e",
                    "name": "Secondary",
                    "slug": "secondary"
                },
                {
                    "color": "#0f3460",
                    "name": "Accent",
                    "slug": "accent"
                },
                {
                    "color": "#e94560",
                    "name": "Highlight",
                    "slug": "highlight"
                },
                {
                    "color": "#ffffff",
                    "name": "Base",
                    "slug": "base"
                },
                {
                    "color": "#f8f9fa",
                    "name": "Base Alt",
                    "slug": "base-alt"
                }
            ]
        },
        "typography": {
            "fluid": true,
            "fontFamilies": [
                {
                    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen-Sans, Ubuntu, Cantarell, 'Helvetica Neue', sans-serif",
                    "name": "System Font",
                    "slug": "system"
                },
                {
                    "fontFamily": "'Inter', sans-serif",
                    "fontFace": [
                        {
                            "fontFamily": "Inter",
                            "fontWeight": "400",
                            "fontStyle": "normal",
                            "src": ["file:./assets/fonts/inter-regular.woff2"]
                        },
                        {
                            "fontFamily": "Inter",
                            "fontWeight": "600",
                            "fontStyle": "normal",
                            "src": ["file:./assets/fonts/inter-semibold.woff2"]
                        },
                        {
                            "fontFamily": "Inter",
                            "fontWeight": "700",
                            "fontStyle": "normal",
                            "src": ["file:./assets/fonts/inter-bold.woff2"]
                        }
                    ],
                    "name": "Inter",
                    "slug": "inter"
                }
            ],
            "fontSizes": [
                {
                    "fluid": {
                        "min": "0.875rem",
                        "max": "1rem"
                    },
                    "name": "Small",
                    "size": "1rem",
                    "slug": "small"
                },
                {
                    "fluid": {
                        "min": "1rem",
                        "max": "1.125rem"
                    },
                    "name": "Medium",
                    "size": "1.125rem",
                    "slug": "medium"
                },
                {
                    "fluid": {
                        "min": "1.25rem",
                        "max": "1.5rem"
                    },
                    "name": "Large",
                    "size": "1.5rem",
                    "slug": "large"
                },
                {
                    "fluid": {
                        "min": "1.75rem",
                        "max": "2.25rem"
                    },
                    "name": "Extra Large",
                    "size": "2.25rem",
                    "slug": "x-large"
                },
                {
                    "fluid": {
                        "min": "2.5rem",
                        "max": "3.5rem"
                    },
                    "name": "Huge",
                    "size": "3.5rem",
                    "slug": "huge"
                }
            ]
        },
        "spacing": {
            "spacingScale": {
                "steps": 7
            },
            "spacingSizes": [
                {
                    "name": "XS",
                    "size": "0.5rem",
                    "slug": "xs"
                },
                {
                    "name": "S",
                    "size": "1rem",
                    "slug": "s"
                },
                {
                    "name": "M",
                    "size": "1.5rem",
                    "slug": "m"
                },
                {
                    "name": "L",
                    "size": "2rem",
                    "slug": "l"
                },
                {
                    "name": "XL",
                    "size": "3rem",
                    "slug": "xl"
                },
                {
                    "name": "XXL",
                    "size": "4rem",
                    "slug": "xxl"
                }
            ],
            "units": ["%", "px", "em", "rem", "vh", "vw"]
        },
        "blocks": {
            "core/button": {
                "border": {
                    "radius": true
                }
            },
            "core/pullquote": {
                "border": {
                    "color": true,
                    "radius": true,
                    "style": true,
                    "width": true
                }
            }
        }
    },
    "styles": {
        "color": {
            "background": "var(--wp--preset--color--base)",
            "text": "var(--wp--preset--color--primary)"
        },
        "typography": {
            "fontFamily": "var(--wp--preset--font-family--system)",
            "fontSize": "var(--wp--preset--font-size--medium)",
            "lineHeight": "1.6"
        },
        "spacing": {
            "padding": {
                "top": "var(--wp--preset--spacing--m)",
                "right": "var(--wp--preset--spacing--m)",
                "bottom": "var(--wp--preset--spacing--m)",
                "left": "var(--wp--preset--spacing--m)"
            }
        },
        "elements": {
            "link": {
                "color": {
                    "text": "var(--wp--preset--color--accent)"
                },
                ":hover": {
                    "color": {
                        "text": "var(--wp--preset--color--highlight)"
                    }
                }
            },
            "button": {
                "border": {
                    "radius": "4px"
                },
                "color": {
                    "background": "var(--wp--preset--color--accent)",
                    "text": "var(--wp--preset--color--base)"
                },
                ":hover": {
                    "color": {
                        "background": "var(--wp--preset--color--highlight)"
                    }
                }
            },
            "heading": {
                "typography": {
                    "fontFamily": "var(--wp--preset--font-family--inter)",
                    "fontWeight": "700",
                    "lineHeight": "1.2"
                }
            },
            "h1": {
                "typography": {
                    "fontSize": "var(--wp--preset--font-size--huge)"
                }
            },
            "h2": {
                "typography": {
                    "fontSize": "var(--wp--preset--font-size--x-large)"
                }
            }
        },
        "blocks": {
            "core/site-title": {
                "typography": {
                    "fontFamily": "var(--wp--preset--font-family--inter)",
                    "fontSize": "var(--wp--preset--font-size--large)",
                    "fontWeight": "700"
                }
            },
            "core/navigation": {
                "typography": {
                    "fontSize": "var(--wp--preset--font-size--small)"
                }
            }
        }
    },
    "templateParts": [
        {
            "area": "header",
            "name": "header",
            "title": "Header"
        },
        {
            "area": "footer",
            "name": "footer",
            "title": "Footer"
        },
        {
            "area": "uncategorized",
            "name": "sidebar",
            "title": "Sidebar"
        }
    ],
    "customTemplates": [
        {
            "name": "blank",
            "postTypes": ["page", "post"],
            "title": "Blank"
        },
        {
            "name": "full-width",
            "postTypes": ["page"],
            "title": "Full Width"
        }
    ]
}
```

### 块模板示例（templates/single.html）

```html
<!-- wp:template-part {"slug":"header","tagName":"header"} /-->

<!-- wp:group {"tagName":"main","layout":{"type":"constrained"}} -->
<main class="wp-block-group">
    <!-- wp:post-featured-image {"align":"wide"} /-->

    <!-- wp:group {"style":{"spacing":{"margin":{"top":"var:preset|spacing|l"}}}} -->
    <div class="wp-block-group">
        <!-- wp:post-title {"level":1} /-->

        <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"},"style":{"spacing":{"blockGap":"var:preset|spacing|s"}}} -->
        <div class="wp-block-group">
            <!-- wp:post-date /-->
            <!-- wp:post-author {"showAvatar":false} /-->
            <!-- wp:post-terms {"term":"category"} /-->
        </div>
        <!-- /wp:group -->
    </div>
    <!-- /wp:group -->

    <!-- wp:post-content {"layout":{"type":"constrained"}} /-->

    <!-- wp:post-terms {"term":"post_tag","prefix":"Tags: "} /-->

    <!-- wp:comments {"className":"wp-block-comments-query-loop"} -->
    <div class="wp-block-comments wp-block-comments-query-loop">
        <!-- wp:comments-title /-->
        <!-- wp:comment-template -->
            <!-- wp:group {"style":{"spacing":{"margin":{"bottom":"var:preset|spacing|m"}}}} -->
            <div class="wp-block-group">
                <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
                <div class="wp-block-group">
                    <!-- wp:avatar {"size":48} /-->
                    <!-- wp:comment-author-name /-->
                    <!-- wp:comment-date /-->
                </div>
                <!-- /wp:group -->
                <!-- wp:comment-content /-->
                <!-- wp:comment-reply-link /-->
            </div>
            <!-- /wp:group -->
        <!-- /wp:comment-template -->
        <!-- wp:comments-pagination -->
            <!-- wp:comments-pagination-previous /-->
            <!-- wp:comments-pagination-numbers /-->
            <!-- wp:comments-pagination-next /-->
        <!-- /wp:comments-pagination -->
        <!-- wp:post-comments-form /-->
    </div>
    <!-- /wp:comments -->
</main>
<!-- /wp:group -->

<!-- wp:template-part {"slug":"footer","tagName":"footer"} /-->
```

### 模板部分示例（parts/header.html）

```html
<!-- wp:group {"tagName":"header","className":"site-header","layout":{"type":"constrained"},"style":{"spacing":{"padding":{"top":"var:preset|spacing|m","bottom":"var:preset|spacing|m"}}}} -->
<header class="wp-block-group site-header">
    <!-- wp:group {"layout":{"type":"flex","justifyContent":"space-between","flexWrap":"wrap"}} -->
    <div class="wp-block-group">
        <!-- wp:group {"layout":{"type":"flex","flexWrap":"nowrap"}} -->
        <div class="wp-block-group">
            <!-- wp:site-logo {"width":50} /-->
            <!-- wp:site-title /-->
        </div>
        <!-- /wp:group -->

        <!-- wp:navigation {"ref":123,"layout":{"type":"flex","setCascadingProperties":true},"style":{"spacing":{"blockGap":"var:preset|spacing|m"}}} /-->
    </div>
    <!-- /wp:group -->
</header>
<!-- /wp:group -->
```

---

## 块模式

### 注册块模式

```php
<?php
/**
 * patterns/hero-section.php
 *
 * Title: Hero Section
 * Slug: theme-name/hero-section
 * Categories: featured, banner
 * Keywords: hero, banner, call to action
 * Block Types: core/template-part/header
 * Viewport Width: 1400
 */

declare(strict_types=1);

defined('ABSPATH') || exit;
?>

<!-- wp:cover {"url":"<?php echo esc_url(get_template_directory_uri()); ?>/assets/images/hero-bg.jpg","dimRatio":60,"overlayColor":"primary","align":"full","style":{"spacing":{"padding":{"top":"var:preset|spacing|xxl","bottom":"var:preset|spacing|xxl"}}}} -->
<div class="wp-block-cover alignfull">
    <span aria-hidden="true" class="wp-block-cover__background has-primary-background-color has-background-dim-60 has-background-dim"></span>
    <img class="wp-block-cover__image-background" src="<?php echo esc_url(get_template_directory_uri()); ?>/assets/images/hero-bg.jpg" alt="" />
    <div class="wp-block-cover__inner-container">
        <!-- wp:group {"layout":{"type":"constrained"}} -->
        <div class="wp-block-group">
            <!-- wp:heading {"textAlign":"center","level":1,"textColor":"base","fontSize":"huge"} -->
            <h1 class="wp-block-heading has-text-align-center has-base-color has-text-color has-huge-font-size"><?php esc_html_e('Welcome to Our Site', 'theme-name'); ?></h1>
            <!-- /wp:heading -->

            <!-- wp:paragraph {"align":"center","textColor":"base","fontSize":"large"} -->
            <p class="has-text-align-center has-base-color has-text-color has-large-font-size"><?php esc_html_e('Discover amazing content and features that will help you succeed.', 'theme-name'); ?></p>
            <!-- /wp:paragraph -->

            <!-- wp:buttons {"layout":{"type":"flex","justifyContent":"center"}} -->
            <div class="wp-block-buttons">
                <!-- wp:button {"backgroundColor":"highlight","textColor":"base"} -->
                <div class="wp-block-button"><a class="wp-block-button__link has-base-color has-highlight-background-color has-text-color has-background wp-element-button"><?php esc_html_e('Get Started', 'theme-name'); ?></a></div>
                <!-- /wp:button -->

                <!-- wp:button {"className":"is-style-outline"} -->
                <div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button"><?php esc_html_e('Learn More', 'theme-name'); ?></a></div>
                <!-- /wp:button -->
            </div>
            <!-- /wp:buttons -->
        </div>
        <!-- /wp:group -->
    </div>
</div>
<!-- /wp:cover -->
```

### 在 functions.php 中注册模式

```php
<?php
/**
 * Register block pattern categories
 */
function register_pattern_categories(): void {
    register_block_pattern_category('theme-name-patterns', [
        'label' => __('Theme Name Patterns', 'theme-name'),
    ]);
}
add_action('init', __NAMESPACE__ . '\\register_pattern_categories');
```

---

## 最佳实践

### 做

- 在块主题中使用 `theme.json` 存储所有设计令牌
- 利用流体排版实现响应式文本
- 为头部/底部创建可重用的模板部分
- 为常见布局注册块模式
- 使用来自 `theme.json` 的 CSS 自定义属性
- 实现适当的可访问性（跳过链接、ARIA）
- 在站点编辑器和前端进行测试

### 不做

- 混合使用传统主题文件和块主题模板
- 在模板中硬编码颜色或大小
- 跳过 `theme.json` 中的 `$schema` 属性
- 忽略模式中的移动端响应式
- 过度覆盖核心块样式
- 忘记在模式中转译可翻译字符串
