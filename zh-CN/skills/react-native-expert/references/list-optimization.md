# 列表优化

## 优化的 FlatList

```typescript
import { FlatList, ListRenderItem } from 'react-native';
import { memo, useCallback } from 'react';

interface Item {
  id: string;
  title: string;
  subtitle: string;
}

// Memoized 列表项
const ListItem = memo(function ListItem({
  item,
  onPress
}: {
  item: Item;
  onPress: (id: string) => void;
}) {
  return (
    <Pressable onPress={() => onPress(item.id)} style={styles.item}>
      <Text style={styles.title}>{item.title}</Text>
      <Text style={styles.subtitle}>{item.subtitle}</Text>
    </Pressable>
  );
});

function OptimizedList({ data }: { data: Item[] }) {
  // Memoize 回调
  const handlePress = useCallback((id: string) => {
    console.log('Selected:', id);
  }, []);

  const renderItem: ListRenderItem<Item> = useCallback(
    ({ item }) => <ListItem item={item} onPress={handlePress} />,
    [handlePress]
  );

  const keyExtractor = useCallback((item: Item) => item.id, []);

  // getItemLayout 的固定高度
  const getItemLayout = useCallback(
    (_: any, index: number) => ({
      length: ITEM_HEIGHT,
      offset: ITEM_HEIGHT * index,
      index,
    }),
    []
  );

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      keyExtractor={keyExtractor}
      getItemLayout={getItemLayout}
      // 性能属性
      removeClippedSubviews
      maxToRenderPerBatch={10}
      windowSize={5}
      initialNumToRender={10}
      updateCellsBatchingPeriod={50}
    />
  );
}

const ITEM_HEIGHT = 72;
```

## SectionList

```typescript
import { SectionList } from 'react-native';

interface Section {
  title: string;
  data: Item[];
}

function GroupedList({ sections }: { sections: Section[] }) {
  const renderSectionHeader = useCallback(
    ({ section }: { section: Section }) => (
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>{section.title}</Text>
      </View>
    ),
    []
  );

  return (
    <SectionList
      sections={sections}
      renderItem={renderItem}
      renderSectionHeader={renderSectionHeader}
      keyExtractor={keyExtractor}
      stickySectionHeadersEnabled
    />
  );
}
```

## 下拉刷新

```typescript
function RefreshableList({ data, onRefresh }: Props) {
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await onRefresh();
    setRefreshing(false);
  }, [onRefresh]);

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          tintColor="#007AFF"
        />
      }
    />
  );
}
```

## 无限滚动

```typescript
function InfiniteList() {
  const [data, setData] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    const newItems = await fetchMoreItems(data.length);

    if (newItems.length === 0) {
      setHasMore(false);
    } else {
      setData(prev => [...prev, ...newItems]);
    }
    setLoading(false);
  }, [data.length, loading, hasMore]);

  const renderFooter = useCallback(() => {
    if (!loading) return null;
    return <ActivityIndicator style={styles.loader} />;
  }, [loading]);

  return (
    <FlatList
      data={data}
      renderItem={renderItem}
      onEndReached={loadMore}
      onEndReachedThreshold={0.5}
      ListFooterComponent={renderFooter}
    />
  );
}
```

## FlashList（替代方案）

```typescript
import { FlashList } from '@shopify/flash-list';

function FastList({ data }: { data: Item[] }) {
  return (
    <FlashList
      data={data}
      renderItem={renderItem}
      estimatedItemSize={72}
      keyExtractor={keyExtractor}
    />
  );
}
```

## 快速参考

| 属性 | 用途 |
|------|---------|
| `removeClippedSubviews` | 卸载屏幕外的项 |
| `maxToRenderPerBatch` | 每批渲染的项数 |
| `windowSize` | 渲染窗口倍数 |
| `initialNumToRender` | 初始渲染的项数 |
| `getItemLayout` | 跳过测量（固定高度） |

| 优化 | 何时使用 |
|--------------|------|
| `memo()` | 所有列表项 |
| `useCallback` | renderItem, keyExtractor |
| `getItemLayout` | 固定高度的项 |
| `FlashList` | 非常大的列表 |
