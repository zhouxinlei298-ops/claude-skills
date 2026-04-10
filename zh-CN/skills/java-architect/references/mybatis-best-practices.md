# MyBatis 最佳实践

## 1. 参数注解使用规范

### 🚨 错误用法
```java
// ❌ 错误：在 Repository 接口中使用 @Param 注解
public interface UserRepository extends JpaRepository<User, Long> {
    List<UserDTO> findByStatus(@Param("status") String status);  // ❌ 错误位置
}
```

### ✅ 正确用法
```java
// ✅ 正确：只在 Mapper 接口（XML 映射）中使用 @Param 注解
@Mapper
public interface ProjectContractMapper extends BaseMapper<ProjectContract> {
    List<WarningSettlementDelayedPO> projectSettlementDelayedDataList(
        @Param("projectStates") List<String> projectStates  // ✅ 正确位置
    );
}

// ✅ 正确：Repository 接口中不使用 @Param 注解
public interface ProjectContractRepository extends IService<ProjectContract> {
    List<WarningSettlementDelayedPO> projectSettlementDelayedDataList(List<String> projectStates);
}

// ✅ 正确：RepositoryImpl 中也不使用 @Param 注解
@Service
public class ProjectContractRepositoryImpl extends ServiceImpl<ProjectContractMapper, ProjectContract> 
    implements ProjectContractRepository {
    
    @Override
    public List<WarningSettlementDelayedPO> projectSettlementDelayedDataList(List<String> projectStates) {
        return baseMapper.projectSettlementDelayedDataList(projectStates);
    }
}
```

### 📚 解释
- @Param 注解是 MyBatis 的注解，用于 XML 映射文件中的参数绑定
- 只有在 Mapper 接口（直接对应 XML 文件的接口）上使用 @Param 注解才有效
- Repository 接口是业务层接口，继承自 IService，不需要也不应该使用 @Param 注解
- Service 调用 Repository 时，直接传递参数即可

## 2. SQL 查询优化技巧

### 使用 IN 查询时注意
```xml
<!-- ✅ 使用 foreach 处理集合 -->
<select id="projectSettlementDelayedDataList" resultType="org.apollo.purchase.entity.project.po.WarningSettlementDelayedPO">
    SELECT
        pc.id AS id,
        p.id AS projectId,
        pc.end_date AS completionDate,
        p.project_code AS projectCode,
        p.project_name AS projectName,
        p.subject_type AS subjectType,
        p.city_code AS cityCode,
        p.county_code AS countyCode,
        p.project_area_code AS projectAreaCode,
        p.competent_unit_type AS competentUnitType,
        p.proprietor_unit_id AS proprietorUnitId,
        p.proprietor_unit_type AS proprietorUnitType,
        p.proprietor_unit_name AS proprietorUnitName,
        p.scope_area_list AS scopeAreaList
    FROM pur_project_contract pc
    INNER JOIN pur_project p ON pc.project_code = p.project_code AND p.is_delete = 0
    LEFT JOIN pur_project_settlement pcs ON pc.project_code = pcs.project_code AND pcs.is_delete = 0
    WHERE
        pc.is_delete = 0
        AND pc.apply_state = 2
        AND pc.end_date IS NOT NULL
        AND p.project_state IN
        <foreach collection="projectStates" item="state" open="(" separator="," close=")">
            #{state}
        </foreach>
        AND pcs.id IS NULL  -- 排除已有结算记录的项目
</select>
```

### 关联查询优化
```xml
<!-- ✅ 使用 LEFT JOIN 排除已记录 -->
SELECT pc.*
FROM pur_project_contract pc
LEFT JOIN pur_project_settlement pcs ON pc.project_code = pcs.project_code AND pcs.is_delete = 0
WHERE pcs.id IS NULL  -- 排除已有结算记录的项目
```

## 3. PO 设计模式

### PO（Persistent Object）的作用
PO 作为数据传输对象，用于接收 SQL 查询的多字段结果，避免多次数据库查询。

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
@Accessors(chain = true)
@ApiModel(value = "WarningSettlementDelayedPO", description = "结算延期预警数据传输对象")
public class WarningSettlementDelayedPO implements Serializable {

    private static final long serialVersionUID = 1L;

    @ApiModelProperty(value = "合同ID")
    private Long id;

    @ApiModelProperty(value = "项目ID")
    private Long projectId;

    @ApiModelProperty("合同完工日期")
    @JsonDeserialize(using = LocalDateDeserializer.class)
    @JsonSerialize(using = LocalDateSerializer.class)
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private LocalDate completionDate;

    // ... 其他字段
}
```

### PO 到 VO 的映射
```java
// PO 到 VO 的映射
return poList.stream()
        .map(po -> {
            WarningSettlementDelayedVO vo = new WarningSettlementDelayedVO();
            vo.setId(po.getId());
            vo.setCompletionDate(po.getCompletionDate());
            
            // 创建 ProjectVO 并映射项目信息
            ProjectVO projectVO = new ProjectVO();
            projectVO.setId(po.getProjectId());
            projectVO.setProjectCode(po.getProjectCode());
            projectVO.setProjectName(po.getProjectName());
            // ... 其他字段映射
            
            vo.setProject(projectVO);
            return vo;
        })
        .collect(Collectors.toList());
```

## 4. 分层架构中的 MyBatis 使用

### 标准分层
```
Controller (HTTP 层)
    ↓
Service (业务逻辑层)
    ↓
Repository (数据仓储层)
    ↓
Mapper (数据访问层)
```

### 各层职责
1. **Mapper 层**：定义 SQL 接口，实现 XML 映射
2. **Repository 层**：封装 CRUD 操作，提供业务数据访问
3. **Service 层**：处理业务逻辑，管理事务
4. **Controller 层**：接收 HTTP 请求，返回响应

## 5. 性能优化建议

### 1. 减少 N+1 查询问题
```xml
<!-- ❌ 避免 N+1 查询 -->
<select id="findProjects" resultType="Project">
    SELECT * FROM projects
</select>

<!-- ✅ 使用 JOIN FETCH 一次性获取关联数据 -->
<select id="findProjectsWithDetails" resultType="ProjectDTO">
    SELECT 
        p.*,
        c.city_name,
        co.county_name
    FROM projects p
    LEFT JOIN cities c ON p.city_id = c.id
    LEFT JOIN counties co ON p.county_id = co.id
    WHERE p.id = #{id}
</select>
```

### 2. 使用批处理
```java
@Service
public class BatchService {
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Transactional
    public void batchInsert(List<Project> projects) {
        jdbcTemplate.batchUpdate("""
            INSERT INTO projects (name, code, status)
            VALUES (?, ?, ?)
            """,
            projects,
            100, // 批量大小
            (ps, project) -> {
                ps.setString(1, project.getName());
                ps.setString(2, project.getCode());
                ps.setString(3, project.getStatus());
            }
        );
    }
}
```

### 3. 合理使用缓存
```java
@Service
@CacheConfig(cacheNames = "projects")
public class ProjectService {
    
    @Cacheable(key = "#id")
    public ProjectDTO getProject(Long id) {
        // 查询逻辑
    }
    
    @CacheEvict(key = "#project.id")
    public ProjectDTO updateProject(ProjectDTO project) {
        // 更新逻辑
    }
    
    @CacheEvict(allEntries = true)
    public void clearCache() {
        // 清除所有缓存
    }
}
```

## 6. 测试策略

### Mapper 层测试
```java
@MybatisTest
@AutoConfigureMybatis
class ProjectContractMapperTest {
    
    @Autowired
    private ProjectContractMapper projectContractMapper;
    
    @Test
    void shouldQuerySettlementDelayedData() {
        // Given
        List<String> projectStates = Arrays.asList("7", "8");
        
        // When
        List<WarningSettlementDelayedPO> result = projectContractMapper.projectSettlementDelayedDataList(projectStates);
        
        // Then
        assertThat(result).isNotEmpty();
        assertThat(result.get(0).getProjectState()).isIn("7", "8");
    }
}
```

### Repository 层测试
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class ProjectContractRepositoryTest {
    
    @Autowired
    private ProjectContractRepository repository;
    
    @Test
    void shouldQueryByProjectStates() {
        // Given
        List<String> projectStates = Arrays.asList("7", "8");
        
        // When
        List<WarningSettlementDelayedPO> result = repository.projectSettlementDelayedDataList(projectStates);
        
        // Then
        assertThat(result).isNotEmpty();
    }
}
```

## 7. 最佳实践总结

1. **分层清晰**：
   - Mapper：处理 SQL 映射
   - Repository：数据仓储，封装 CRUD
   - Service：业务逻辑处理

2. **注解使用规范**：
   - MyBatis 注解（@Param、@Select 等）只在 Mapper 层使用
   - Spring 注解（@Service、@Autowired 等）在相应层使用

3. **性能优化**：
   - 尽量在 SQL 层完成过滤，减少数据传输
   - 使用 JOIN 代替多次查询
   - 合理使用缓存和批处理

4. **错误处理**：
   - 在 Service 层处理业务异常
   - 使用全局异常处理器统一返回错误信息

5. **代码规范**：
   - PO 类使用 Lombok 简化代码
   - 使用 @ApiModelProperty 注解提供 API 文档
   - LocalDate 类型字段添加 JSON 序列化注解