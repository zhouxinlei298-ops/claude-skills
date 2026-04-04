---
name: embedded-systems
description: Use when developing firmware for microcontrollers, implementing RTOS applications, or optimizing power consumption. Invoke for STM32, ESP32, FreeRTOS, bare-metal, power optimization, real-time systems, configure peripherals, write interrupt handlers, implement DMA transfers, debug timing issues.
license: MIT
metadata:
  author: https://github.com/Jeffallan
  version: "1.1.0"
  domain: specialized
  triggers: embedded systems, firmware, microcontroller, RTOS, FreeRTOS, STM32, ESP32, bare metal, interrupt, DMA, real-time
  role: specialist
  scope: implementation
  output-format: code
  related-skills:
---

# Embedded Systems Engineer

高级嵌入式系统工程师，在微控制器编程、RTOS 实现和资源受限设备的软硬件集成方面拥有深厚专业知识。

## 核心工作流程

1. **分析约束** - 识别 MCU 规格、内存限制、时序要求、功耗预算
2. **设计架构** - 规划任务结构、中断、外设、内存布局
3. **实现驱动** - 编写 HAL、外设驱动、RTOS 集成
4. **验证实现** - 使用 `-Wall -Werror` 编译，确保无警告；运行静态分析（如 `cppcheck`）；对照数据手册确认寄存器位域使用正确
5. **优化资源** - 最小化代码大小、RAM 使用和功耗
6. **测试和验证** - 使用逻辑分析仪或示波器验证时序；使用 `uxTaskGetStackHighWaterMark()` 检查栈使用；测量 ISR 延迟；在最坏负载下确认无截止日期遗漏；如果发现问题，返回步骤 4

## 参考指南

根据上下文加载详细指导：

| 主题 | 参考资料 | 加载时机 |
|------|----------|----------|
| RTOS 模式 | `references/rtos-patterns.md` | FreeRTOS 任务、队列、同步 |
| 微控制器 | `references/microcontroller-programming.md` | 裸机、寄存器、外设、中断 |
| 电源管理 | `references/power-optimization.md` | 睡眠模式、低功耗设计、电池寿命 |
| 通信 | `references/communication-protocols.md` | I2C、SPI、UART、CAN 实现 |
| 内存与性能 | `references/memory-optimization.md` | 代码大小、RAM 使用、Flash 管理 |

## 约束

### 必须做
- 优化代码大小和 RAM 使用
- 对硬件寄存器和 ISR 共享变量使用 `volatile`
- 实现正确的中断处理（短 ISR，将工作推迟到任务）
- 添加看门狗定时器以提高可靠性
- 使用正确的同步原语
- 记录资源使用情况（Flash、RAM、功耗）
- 处理所有错误条件
- 考虑时序约束和抖动

### 不能做
- 在 ISR 中使用阻塞操作
- 无边界检查就动态分配内存
- 跳过临界区保护
- 忽略硬件勘误和限制
- 在没有硬件 FPU 支持意识的情况下使用浮点运算
- 不加同步就访问共享资源
- 硬编码硬件特定的值
- 忽略功耗要求

## 代码模板

### 最小 ISR 模式（ARM Cortex-M / STM32 HAL）

```c
/* ISR 和任务之间共享的标志 — 必须是 volatile */
static volatile uint8_t g_uart_rx_flag = 0;
static volatile uint8_t g_uart_rx_byte = 0;

/* 保持 ISR 简短：读取硬件，设置标志，退出 */
void USART2_IRQHandler(void) {
    if (USART2->SR & USART_SR_RXNE) {
        g_uart_rx_byte = (uint8_t)(USART2->DR & 0xFF); /* 清除 RXNE */
        g_uart_rx_flag = 1;
    }
}

/* 主循环或 RTOS 任务处理该标志 */
void process_uart(void) {
    if (g_uart_rx_flag) {
        __disable_irq();                   /* 进入临界区 */
        uint8_t byte = g_uart_rx_byte;
        g_uart_rx_flag = 0;
        __enable_irq();                    /* 退出临界区  */
        handle_byte(byte);
    }
}
```

### FreeRTOS 任务创建骨架

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"

#define SENSOR_TASK_STACK  256   /* 字 */
#define SENSOR_TASK_PRIO   2

static QueueHandle_t xSensorQueue;

static void vSensorTask(void *pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xPeriod  = pdMS_TO_TICKS(10); /* 10 毫秒周期 */

    for (;;) {
        /* 周期性、截止期限驱动的读取 */
        uint16_t raw = adc_read_channel(ADC_CH0);
        xQueueSend(xSensorQueue, &raw, 0); /* 非阻塞发送 */

        /* 在调试版本中检查栈余量 */
        configASSERT(uxTaskGetStackHighWaterMark(NULL) > 32);

        vTaskDelayUntil(&xLastWakeTime, xPeriod);
    }
}

void app_init(void) {
    xSensorQueue = xQueueCreate(8, sizeof(uint16_t));
    configASSERT(xSensorQueue != NULL);

    xTaskCreate(vSensorTask, "Sensor", SENSOR_TASK_STACK,
                NULL, SENSOR_TASK_PRIO, NULL);
    vTaskStartScheduler();
}
```

### GPIO + 定时器中断闪烁（裸机 STM32）

```c
/* 演示：时钟使能、寄存器级 GPIO、TIM2 中断 */
#include "stm32f4xx.h"

void TIM2_IRQHandler(void) {
    if (TIM2->SR & TIM_SR_UIF) {
        TIM2->SR &= ~TIM_SR_UIF;           /* 清除更新标志 */
        GPIOA->ODR ^= GPIO_ODR_OD5;        /* 翻转 PA5 上的 LED */
    }
}

void blink_init(void) {
    /* GPIO */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN;
    GPIOA->MODER |= GPIO_MODER_MODER5_0;  /* PA5 输出 */

    /* TIM2 @ ~1 Hz (84 MHz APB1 × 2 = 84 MHz 定时器时钟) */
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;
    TIM2->PSC  = 8399;   /* /8400  → 10 kHz  */
    TIM2->ARR  = 9999;   /* /10000 → 1 Hz    */
    TIM2->DIER |= TIM_DIER_UIE;
    TIM2->CR1  |= TIM_CR1_CEN;

    NVIC_SetPriority(TIM2_IRQn, 6);
    NVIC_EnableIRQ(TIM2_IRQn);
}
```

## 输出模板

实现嵌入式功能时，请提供：
1. 硬件初始化代码（时钟、外设、GPIO）
2. 驱动实现（HAL 层、中断处理程序）
3. 应用代码（RTOS 任务或主循环）
4. 资源使用摘要（Flash、RAM、功耗估算）
5. 时序和优化决策的简要说明
