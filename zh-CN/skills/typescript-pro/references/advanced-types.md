# 高级类型

## 泛型约束

```typescript
// Basic constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

// Multiple constraints
interface HasId { id: number; }
interface HasName { name: string; }

function merge<T extends HasId, U extends HasName>(obj1: T, obj2: U): T & U {
  return { ...obj1, ...obj2 };
}

// Generic constraint with default
type ApiResponse<T = unknown, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

// Constraint with infer
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;
type Result = UnwrapPromise<Promise<string>>; // string
```

## 条件类型

```typescript
// Basic conditional type
type IsString<T> = T extends string ? true : false;

// Distributive conditional types
type ToArray<T> = T extends any ? T[] : never;
type StringOrNumberArray = ToArray<string | number>; // string[] | number[]

// Non-distributive (use tuple)
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;
type BothArray = ToArrayNonDist<string | number>; // (string | number)[]

// Nested conditionals for type extraction
type Flatten<T> = T extends Array<infer U>
  ? U extends Array<infer V>
    ? Flatten<V>
    : U
  : T;

type Nested = Flatten<string[][][]>; // string

// Exclude null/undefined
type NonNullable<T> = T extends null | undefined ? never : T;
```

## 映射类型

```typescript
// Basic mapped type
type ReadOnly<T> = {
  readonly [K in keyof T]: T[K];
};

// Optional properties
type Partial<T> = {
  [K in keyof T]?: T[K];
};

// Required properties
type Required<T> = {
  [K in keyof T]-?: T[K]; // Remove optional modifier
};

// Key remapping with 'as'
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

interface Person {
  name: string;
  age: number;
}

type PersonGetters = Getters<Person>;
// { getName: () => string; getAge: () => number; }

// Filtering keys
type PickByType<T, U> = {
  [K in keyof T as T[K] extends U ? K : never]: T[K];
};

type StringFields = PickByType<Person, string>; // { name: string }
```

## 模板字面量类型

```typescript
// Basic template literal
type EmailLocale = 'en' | 'es' | 'fr';
type EmailType = 'welcome' | 'reset-password';
type EmailTemplate = `${EmailLocale}_${EmailType}`;
// 'en_welcome' | 'en_reset-password' | 'es_welcome' | ...

// Intrinsic string manipulation
type Uppercase<S extends string> = intrinsic;
type Lowercase<S extends string> = intrinsic;
type Capitalize<S extends string> = intrinsic;
type Uncapitalize<S extends string> = intrinsic;

type EventName<T extends string> = `on${Capitalize<T>}`;
type ClickEvent = EventName<'click'>; // 'onClick'

// Template literal with mapped types
type CSSProperties = {
  [K in 'color' | 'background' | 'border' as `--${K}`]: string;
};
// { '--color': string; '--background': string; '--border': string }

// Pattern matching with infer
type ExtractRouteParams<T extends string> =
  T extends `${infer _Start}/:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<`/${Rest}`>
    : T extends `${infer _Start}/:${infer Param}`
    ? Param
    : never;

type Params = ExtractRouteParams<'/users/:id/posts/:postId'>; // 'id' | 'postId'
```

## 高阶类型（模拟）

```typescript
// Type-level function simulation
interface TypeClass<F> {
  map: <A, B>(f: (a: A) => B, fa: any) => any;
}

// Functor pattern
type Maybe<T> = { type: 'just'; value: T } | { type: 'nothing' };

const MaybeFunctor: TypeClass<Maybe<any>> = {
  map: <A, B>(f: (a: A) => B, ma: Maybe<A>): Maybe<B> => {
    return ma.type === 'just'
      ? { type: 'just', value: f(ma.value) }
      : { type: 'nothing' };
  }
};

// Builder pattern with generics
type Builder<T, K extends keyof T = never> = {
  with<P extends Exclude<keyof T, K>>(
    key: P,
    value: T[P]
  ): Builder<T, K | P>;
  build(): K extends keyof T ? T : never;
};
```

## 递归类型

```typescript
// JSON type
type JSONValue =
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

// Deep partial
type DeepPartial<T> = T extends object ? {
  [K in keyof T]?: DeepPartial<T[K]>;
} : T;

// Deep readonly
type DeepReadonly<T> = T extends object ? {
  readonly [K in keyof T]: DeepReadonly<T[K]>;
} : T;

// Path type for nested objects
type PathsToProps<T> = T extends object ? {
  [K in keyof T]: K extends string
    ? T[K] extends object
      ? K | `${K}.${PathsToProps<T[K]>}`
      : K
    : never;
}[keyof T] : never;

interface User {
  profile: {
    name: string;
    settings: {
      theme: string;
    };
  };
}

type UserPaths = PathsToProps<User>;
// 'profile' | 'profile.name' | 'profile.settings' | 'profile.settings.theme'
```

## 协变与逆变

```typescript
// Covariance (return types)
type Producer<T> = () => T;
let stringProducer: Producer<string> = () => 'hello';
let objectProducer: Producer<object> = stringProducer; // OK: string is object

// Contravariance (parameter types)
type Consumer<T> = (value: T) => void;
let objectConsumer: Consumer<object> = (obj) => console.log(obj);
let stringConsumer: Consumer<string> = objectConsumer; // OK in strict mode

// Invariance (mutable properties)
interface Box<T> {
  value: T;
  setValue(v: T): void;
}

let stringBox: Box<string> = { value: '', setValue: (v) => {} };
// let objectBox: Box<object> = stringBox; // Error: invariant
```

## 类型级编程

```typescript
// Type-level addition (limited)
type Length<T extends any[]> = T['length'];
type Concat<A extends any[], B extends any[]> = [...A, ...B];

// Type-level conditionals
type If<Condition extends boolean, Then, Else> =
  Condition extends true ? Then : Else;

// Type-level equality
type Equal<X, Y> =
  (<T>() => T extends X ? 1 : 2) extends
  (<T>() => T extends Y ? 1 : 2) ? true : false;

// Assert equal types (for testing)
type Assert<T extends true> = T;
type Test = Assert<Equal<1 | 2, 2 | 1>>; // OK
```

## 快速参考

| 模式 | 用途 |
|------|------|
| `T extends U ? X : Y` | 条件类型逻辑 |
| `infer R` | 从模式中提取类型 |
| `K in keyof T` | 迭代对象键 |
| `as NewKey` | 在映射类型中重新映射键 |
| 模板字面量 | 字符串模式类型 |
| `T extends any` | 分布式条件类型 |
| `[T] extends [any]` | 非分布式检查 |
| `-?` 修饰符 | 移除可选标记 |
| `readonly` 修饰符 | 使属性不可变 |
