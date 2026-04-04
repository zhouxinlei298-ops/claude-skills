# Storefront API

---

## 何时使用

- 使用 React、Next.js 或 Hydrogen 构建 headless 商店前端
- 创建自定义结账体验
- 构建连接到 Shopify 的移动应用
- 实现实时库存或价格功能
- 创建使用 Shopify 后端的 PWA

## 何时不使用

- 标准主题定制（使用 Liquid）
- 管理操作（使用 Admin API）
- 后端 webhook 处理（使用 Admin API）
- 简单的产品展示（Liquid 更快）

---

## API 基础

### 身份验证

```typescript
// Storefront API uses public access tokens (safe for client-side)
const STOREFRONT_ACCESS_TOKEN = 'your-storefront-access-token';
const SHOP_DOMAIN = 'your-store.myshopify.com';
const API_VERSION = '2024-10'; // Use latest stable version

// GraphQL endpoint
const endpoint = `https://${SHOP_DOMAIN}/api/${API_VERSION}/graphql.json`;

// Basic fetch wrapper
async function storefrontFetch<T>(query: string, variables?: Record<string, unknown>): Promise<T> {
  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Storefront-Access-Token': STOREFRONT_ACCESS_TOKEN,
    },
    body: JSON.stringify({ query, variables }),
  });

  const json = await response.json();

  if (json.errors) {
    throw new Error(json.errors.map((e: { message: string }) => e.message).join(', '));
  }

  return json.data;
}
```

### 速率限制

- **面向买家**：每秒 2000 个成本点（所有客户端共享）
- **每个查询都有成本**：简单查询约 1-10 个点，复杂查询约 50-100+
- **在响应中检查成本**：

```typescript
// Include cost in query
const query = `
  query Products @inContext(country: US, language: EN) {
    products(first: 10) {
      edges { node { id title } }
    }
  }
`;

// Response includes:
// "extensions": {
//   "cost": {
//     "requestedQueryCost": 12,
//     "actualQueryCost": 12,
//     "throttleStatus": {
//       "maximumAvailable": 2000,
//       "currentlyAvailable": 1988,
//       "restoreRate": 100
//     }
//   }
// }
```

---

## Hydrogen 2024（基于 Remix）

### 项目设置

```bash
# Create new Hydrogen project
npm create @shopify/hydrogen@latest -- --template demo-store

# Project structure
hydrogen-storefront/
├── app/
│   ├── components/      # React components
│   ├── lib/             # Utilities, fragments
│   ├── routes/          # Remix routes
│   └── styles/          # CSS
├── public/              # Static assets
├── server.ts            # Entry point
└── hydrogen.config.ts   # Hydrogen config
```

### Hydrogen 配置

```typescript
// hydrogen.config.ts
import {defineConfig} from '@shopify/hydrogen/config';

export default defineConfig({
  shopify: {
    storeDomain: 'your-store.myshopify.com',
    storefrontToken: process.env.PUBLIC_STOREFRONT_API_TOKEN!,
    storefrontApiVersion: '2024-10',
  },
  session: {
    storage: 'cookie', // or 'memory' for development
  },
});
```

### 带数据加载的路由

```typescript
// app/routes/products.$handle.tsx
import {useLoaderData, type MetaFunction} from '@remix-run/react';
import {json, type LoaderFunctionArgs} from '@shopify/remix-oxygen';
import {
  Image,
  Money,
  VariantSelector,
  getSelectedProductOptions,
} from '@shopify/hydrogen';
import type {ProductQuery} from 'storefrontapi.generated';

export const meta: MetaFunction<typeof loader> = ({data}) => {
  return [{title: data?.product?.title ?? 'Product'}];
};

export async function loader({params, request, context}: LoaderFunctionArgs) {
  const {handle} = params;
  const {storefront} = context;

  const selectedOptions = getSelectedProductOptions(request);

  const {product} = await storefront.query<ProductQuery>(PRODUCT_QUERY, {
    variables: {
      handle,
      selectedOptions,
      country: context.storefront.i18n.country,
      language: context.storefront.i18n.language,
    },
  });

  if (!product?.id) {
    throw new Response('Product not found', {status: 404});
  }

  return json({product});
}

export default function Product() {
  const {product} = useLoaderData<typeof loader>();
  const {title, descriptionHtml, featuredImage, variants} = product;

  return (
    <div className="product-page">
      <div className="product-image">
        {featuredImage && (
          <Image
            data={featuredImage}
            sizes="(min-width: 768px) 50vw, 100vw"
            aspectRatio="1/1"
          />
        )}
      </div>

      <div className="product-info">
        <h1>{title}</h1>

        <VariantSelector
          handle={product.handle}
          options={product.options}
          variants={variants}
        >
          {({option}) => (
            <div key={option.name} className="option-group">
              <h3>{option.name}</h3>
              <div className="option-values">
                {option.values.map(({value, isAvailable, to}) => (
                  <a
                    key={value}
                    href={to}
                    className={`option-value ${!isAvailable ? 'unavailable' : ''}`}
                  >
                    {value}
                  </a>
                ))}
              </div>
            </div>
          )}
        </VariantSelector>

        <ProductPrice selectedVariant={product.selectedVariant} />

        <AddToCartButton
          lines={[
            {
              merchandiseId: product.selectedVariant?.id,
              quantity: 1,
            },
          ]}
          disabled={!product.selectedVariant?.availableForSale}
        />

        <div
          className="product-description"
          dangerouslySetInnerHTML={{__html: descriptionHtml}}
        />
      </div>
    </div>
  );
}

const PRODUCT_QUERY = `#graphql
  query Product(
    $handle: String!
    $selectedOptions: [SelectedOptionInput!]!
    $country: CountryCode
    $language: LanguageCode
  ) @inContext(country: $country, language: $language) {
    product(handle: $handle) {
      id
      title
      handle
      descriptionHtml
      featuredImage {
        url
        altText
        width
        height
      }
      options {
        name
        values
      }
      selectedVariant: variantBySelectedOptions(selectedOptions: $selectedOptions) {
        id
        availableForSale
        price {
          amount
          currencyCode
        }
        compareAtPrice {
          amount
          currencyCode
        }
        selectedOptions {
          name
          value
        }
      }
      variants(first: 100) {
        nodes {
          id
          availableForSale
          selectedOptions {
            name
            value
          }
        }
      }
    }
  }
`;
```

---

## 核心 GraphQL 模式

### 带分页的产品查询

```graphql
query Products(
  $first: Int!
  $after: String
  $query: String
  $sortKey: ProductSortKeys
  $reverse: Boolean
  $country: CountryCode
  $language: LanguageCode
) @inContext(country: $country, language: $language) {
  products(
    first: $first
    after: $after
    query: $query
    sortKey: $sortKey
    reverse: $reverse
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        handle
        title
        description
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
          maxVariantPrice {
            amount
            currencyCode
          }
        }
        featuredImage {
          url(transform: { maxWidth: 400, maxHeight: 400 })
          altText
        }
        variants(first: 1) {
          nodes {
            id
            availableForSale
          }
        }
      }
    }
  }
}
```

### 带过滤器的集合

```graphql
query Collection(
  $handle: String!
  $first: Int!
  $after: String
  $filters: [ProductFilter!]
  $sortKey: ProductCollectionSortKeys
  $reverse: Boolean
  $country: CountryCode
  $language: LanguageCode
) @inContext(country: $country, language: $language) {
  collection(handle: $handle) {
    id
    title
    description
    image {
      url
      altText
    }
    products(
      first: $first
      after: $after
      filters: $filters
      sortKey: $sortKey
      reverse: $reverse
    ) {
      filters {
        id
        label
        type
        values {
          id
          label
          count
          input
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        ...ProductCard
      }
    }
  }
}

fragment ProductCard on Product {
  id
  handle
  title
  featuredImage {
    url(transform: { maxWidth: 300 })
    altText
  }
  priceRange {
    minVariantPrice {
      amount
      currencyCode
    }
  }
  variants(first: 1) {
    nodes {
      availableForSale
    }
  }
}
```

### 购物车操作

```typescript
// Create cart
const CREATE_CART = `#graphql
  mutation CartCreate($input: CartInput!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartCreate(input: $input) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Add to cart
const ADD_TO_CART = `#graphql
  mutation CartLinesAdd($cartId: ID!, $lines: [CartLineInput!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesAdd(cartId: $cartId, lines: $lines) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Update cart line
const UPDATE_CART_LINES = `#graphql
  mutation CartLinesUpdate($cartId: ID!, $lines: [CartLineUpdateInput!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesUpdate(cartId: $cartId, lines: $lines) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Remove from cart
const REMOVE_FROM_CART = `#graphql
  mutation CartLinesRemove($cartId: ID!, $lineIds: [ID!]!, $country: CountryCode, $language: LanguageCode)
  @inContext(country: $country, language: $language) {
    cartLinesRemove(cartId: $cartId, lineIds: $lineIds) {
      cart {
        ...CartFragment
      }
      userErrors {
        field
        message
      }
    }
  }
`;

// Cart fragment for consistent data
const CART_FRAGMENT = `#graphql
  fragment CartFragment on Cart {
    id
    checkoutUrl
    totalQuantity
    cost {
      subtotalAmount {
        amount
        currencyCode
      }
      totalAmount {
        amount
        currencyCode
      }
      totalTaxAmount {
        amount
        currencyCode
      }
    }
    lines(first: 100) {
      nodes {
        id
        quantity
        cost {
          totalAmount {
            amount
            currencyCode
          }
        }
        merchandise {
          ... on ProductVariant {
            id
            title
            image {
              url(transform: { maxWidth: 100 })
              altText
            }
            product {
              title
              handle
            }
            price {
              amount
              currencyCode
            }
          }
        }
        attributes {
          key
          value
        }
      }
    }
    discountCodes {
      code
      applicable
    }
  }
`;
```

---

## 客户身份验证

### 客户账户 API（2024+）

```typescript
// New Customer Account API for headless auth
const CUSTOMER_LOGIN = `#graphql
  mutation CustomerAccessTokenCreate($input: CustomerAccessTokenCreateInput!) {
    customerAccessTokenCreate(input: $input) {
      customerAccessToken {
        accessToken
        expiresAt
      }
      customerUserErrors {
        code
        field
        message
      }
    }
  }
`;

// Get customer with token
const GET_CUSTOMER = `#graphql
  query Customer($customerAccessToken: String!) {
    customer(customerAccessToken: $customerAccessToken) {
      id
      firstName
      lastName
      email
      phone
      acceptsMarketing
      defaultAddress {
        ...AddressFragment
      }
      addresses(first: 10) {
        nodes {
          ...AddressFragment
        }
      }
      orders(first: 10, sortKey: PROCESSED_AT, reverse: true) {
        nodes {
          id
          orderNumber
          processedAt
          financialStatus
          fulfillmentStatus
          totalPrice {
            amount
            currencyCode
          }
          lineItems(first: 5) {
            nodes {
              title
              quantity
              variant {
                image {
                  url(transform: { maxWidth: 100 })
                }
              }
            }
          }
        }
      }
    }
  }

  fragment AddressFragment on MailingAddress {
    id
    address1
    address2
    city
    province
    country
    zip
    phone
  }
`;

// Customer registration
const CUSTOMER_CREATE = `#graphql
  mutation CustomerCreate($input: CustomerCreateInput!) {
    customerCreate(input: $input) {
      customer {
        id
        email
        firstName
        lastName
      }
      customerUserErrors {
        code
        field
        message
      }
    }
  }
`;
```

---

## 国际化

### 市场感知查询

```typescript
// Always use @inContext directive for localization
const LOCALIZED_PRODUCTS = `#graphql
  query Products($country: CountryCode!, $language: LanguageCode!)
  @inContext(country: $country, language: $language) {
    products(first: 10) {
      nodes {
        title  # Returns translated title
        priceRange {
          minVariantPrice {
            amount      # Returns price in local currency
            currencyCode
          }
        }
      }
    }
  }
`;

// Get available markets
const GET_LOCALIZATION = `#graphql
  query Localization {
    localization {
      availableCountries {
        isoCode
        name
        currency {
          isoCode
          name
          symbol
        }
        availableLanguages {
          isoCode
          name
        }
      }
      country {
        isoCode
        name
        currency {
          isoCode
          symbol
        }
      }
      language {
        isoCode
        name
      }
    }
  }
`;
```

### Hydrogen 本地化

```typescript
// app/routes/($locale).products._index.tsx
import {type LoaderFunctionArgs} from '@shopify/remix-oxygen';

export async function loader({params, context}: LoaderFunctionArgs) {
  const {locale} = params;
  const {storefront} = context;

  // Storefront client automatically handles locale from route
  const {products} = await storefront.query(PRODUCTS_QUERY, {
    variables: {
      country: storefront.i18n.country,
      language: storefront.i18n.language,
    },
  });

  return json({products});
}

// server.ts - Configure i18n
const i18n = {
  default: {language: 'EN', country: 'US'},
  subfolders: [
    {language: 'FR', country: 'FR', pathPrefix: '/fr-fr'},
    {language: 'DE', country: 'DE', pathPrefix: '/de-de'},
    {language: 'EN', country: 'GB', pathPrefix: '/en-gb'},
  ],
};
```

---

## 搜索和预测搜索

```graphql
# Full search
query Search($query: String!, $first: Int!, $types: [SearchType!]) {
  search(query: $query, first: $first, types: $types) {
    totalCount
    nodes {
      ... on Product {
        __typename
        id
        handle
        title
        featuredImage {
          url(transform: { maxWidth: 200 })
        }
        priceRange {
          minVariantPrice {
            amount
            currencyCode
          }
        }
      }
      ... on Article {
        __typename
        id
        handle
        title
        blog {
          handle
        }
      }
      ... on Page {
        __typename
        id
        handle
        title
      }
    }
  }
}

# Predictive search (faster, for autocomplete)
query PredictiveSearch($query: String!, $limit: Int!) {
  predictiveSearch(query: $query, limit: $limit, limitScope: EACH) {
    products {
      id
      handle
      title
      featuredImage {
        url(transform: { maxWidth: 100 })
      }
      priceRange {
        minVariantPrice {
          amount
          currencyCode
        }
      }
    }
    collections {
      id
      handle
      title
    }
    queries {
      text
      styledText
    }
  }
}
```

---

## 性能优化

### 查询最佳实践

```typescript
// BAD: Over-fetching
const BAD_QUERY = `#graphql
  query Product($handle: String!) {
    product(handle: $handle) {
      id
      title
      description
      descriptionHtml
      vendor
      productType
      tags
      # Fetching ALL variants when you only need first
      variants(first: 250) {
        nodes {
          id
          title
          price { amount currencyCode }
          compareAtPrice { amount currencyCode }
          image { url altText width height }
          selectedOptions { name value }
          sku
          barcode
          weight
          weightUnit
        }
      }
      # Fetching ALL images
      images(first: 250) {
        nodes {
          url
          altText
          width
          height
        }
      }
    }
  }
`;

// GOOD: Fetch only what you need
const GOOD_QUERY = `#graphql
  query Product($handle: String!) {
    product(handle: $handle) {
      id
      title
      descriptionHtml
      featuredImage {
        url(transform: { maxWidth: 800 })
        altText
      }
      # Only fetch what's visible
      variants(first: 10) {
        nodes {
          id
          availableForSale
          price { amount currencyCode }
          selectedOptions { name value }
        }
      }
    }
  }
`;

// Use fragments for reusability and consistency
const PRODUCT_CARD_FRAGMENT = `#graphql
  fragment ProductCard on Product {
    id
    handle
    title
    featuredImage {
      url(transform: { maxWidth: 300, maxHeight: 300 })
      altText
    }
    priceRange {
      minVariantPrice {
        amount
        currencyCode
      }
    }
    variants(first: 1) {
      nodes {
        availableForSale
      }
    }
  }
`;
```

### 缓存策略

```typescript
// Hydrogen caching
export async function loader({context}: LoaderFunctionArgs) {
  const {storefront} = context;

  // Short cache for frequently changing data
  const {products} = await storefront.query(PRODUCTS_QUERY, {
    cache: storefront.CacheShort(), // ~1 minute
  });

  // Long cache for static content
  const {menu} = await storefront.query(MENU_QUERY, {
    cache: storefront.CacheLong(), // ~1 hour
  });

  // No cache for user-specific data
  const {customer} = await storefront.query(CUSTOMER_QUERY, {
    cache: storefront.CacheNone(),
  });

  return json({products, menu, customer});
}
```

---

## 相关参考

- **Liquid Templating** - 用于基于主题的实现
- **App Development** - 用于 Admin API 和后端集成
- **Checkout Customization** - 用于使用 Storefront API 的结账扩展
- **Performance Optimization** - 详细的性能模式