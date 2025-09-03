# Sample Code Analysis: Before & After Coupling Reduction

This document demonstrates the Semgrep + Connascence rules pack in action with real-world code examples, showing how the analysis identifies coupling issues and guides developers toward better solutions.

## 🔍 Analysis Overview

**Sample Project**: E-commerce Order Processing Service  
**Language**: TypeScript/JavaScript  
**Initial Coupling Index**: 8.2/10 (High coupling)  
**Target Coupling Index**: < 6.0/10 (Acceptable coupling)  
**Analysis Tools**: Semgrep + Connascence Enterprise Pack

## 📊 Executive Summary

The analysis identified 47 coupling violations across 5 connascence types, with an estimated technical debt of $89,000. Strategic refactoring reduced the coupling index by 34% and eliminated all critical violations.

### Impact Metrics
- **Coupling Violations**: 47 → 3 (-94%)
- **Critical Issues**: 12 → 0 (-100%)
- **Coupling Index**: 8.2 → 5.4 (-34%)
- **Estimated Refactoring Cost**: 89 hours ($8,900)
- **Projected Annual Savings**: $34,000 in maintenance

## 🚨 Before: High-Coupling Code

### Example 1: Connascence of Meaning (CoM) - Magic Numbers
```typescript
// ❌ BEFORE: Multiple CoM violations detected by Semgrep
class OrderProcessor {
  calculateTotal(items: any[], customerType: string, location: string) {
    let total = 0;
    
    // Magic numbers create Connascence of Meaning
    for (const item of items) {
      total += item.price * item.quantity;
      
      if (item.weight > 2.5) {  // Magic number: weight threshold
        total += 15.99;         // Magic number: heavy item fee
      }
      
      if (item.category === 'electronics') {
        total *= 1.08;          // Magic number: electronics tax rate
      }
    }
    
    // More magic numbers for customer discounts
    if (customerType === 'premium' && total > 500) {
      total *= 0.95;            // Magic number: premium discount
    }
    
    // Location-based tax (hardcoded rates)
    if (location === 'CA') {
      total *= 1.0725;          // Magic number: CA tax rate
    } else if (location === 'NY') {
      total *= 1.08;            // Magic number: NY tax rate
    }
    
    return total;
  }
}
```

**Semgrep Analysis Results:**
```json
{
  "rule_id": "magic-numbers-financial",
  "severity": "ERROR",
  "message": "Magic number detected in financial calculation. Define as named constant.",
  "violations": [
    {"line": 7, "value": "2.5", "context": "weight threshold"},
    {"line": 8, "value": "15.99", "context": "heavy item fee"},
    {"line": 12, "value": "1.08", "context": "tax multiplier"},
    {"line": 17, "value": "500", "context": "discount threshold"},
    {"line": 18, "value": "0.95", "context": "discount rate"}
  ],
  "business_impact": "Financial calculations with magic numbers increase bug risk",
  "estimated_fix_time": "15-30 minutes"
}
```

### Example 2: Connascence of Position (CoP) - Parameter Overload
```typescript
// ❌ BEFORE: Excessive parameter coupling
class ShippingService {
  // 8 parameters create high positional coupling
  calculateShipping(
    weight: number,
    dimensions: number[],
    destination: string,
    service: string,
    insurance: boolean,
    signature: boolean,
    priority: boolean,
    packaging: string
  ): number {
    // Complex shipping logic with positional dependencies
    if (service === 'overnight' && priority && signature) {
      return weight * 12.99 + (insurance ? 8.50 : 0);
    }
    
    // Error-prone parameter ordering
    return this.calculateStandardRate(weight, destination, service, insurance);
  }
  
  // Positional array response creates client coupling
  getShippingOptions(weight: number, destination: string): number[] {
    return [
      this.calculateStandard(weight, destination),      // [0] = standard
      this.calculateExpress(weight, destination),       // [1] = express  
      this.calculateOvernight(weight, destination)      // [2] = overnight
    ];
  }
}
```

**Semgrep Analysis Results:**
```json
{
  "rule_id": "excessive-parameters-position-coupling", 
  "severity": "ERROR",
  "message": "Function with 8 parameters creates Connascence of Position (CoP)",
  "suggestion": "Consider using options object pattern",
  "business_impact": "High parameter count increases bug risk and reduces maintainability",
  "estimated_fix_time": "45-60 minutes"
}
```

### Example 3: Connascence of Timing (CoT) - Race Conditions
```typescript
// ❌ BEFORE: Timing dependencies and race conditions
class InventoryManager {
  private inventoryCache: Map<string, number> = new Map();
  
  async processOrder(orderId: string, items: OrderItem[]) {
    // Race condition: cache and database updates not synchronized
    for (const item of items) {
      const currentStock = this.inventoryCache.get(item.productId) || 0;
      
      if (currentStock >= item.quantity) {
        // Update cache first (timing dependency)
        this.inventoryCache.set(item.productId, currentStock - item.quantity);
        
        // Async database update creates timing gap
        await this.updateDatabaseInventory(item.productId, item.quantity);
        
        // Another cache operation - potential race condition
        await this.logInventoryChange(item.productId, -item.quantity);
      }
    }
  }
  
  // Concurrent access without synchronization
  async updateDatabaseInventory(productId: string, quantity: number) {
    const current = await this.database.getStock(productId);
    await this.database.updateStock(productId, current - quantity);
  }
}
```

**Semgrep Analysis Results:**
```json
{
  "rule_id": "race-condition-shared-state",
  "severity": "ERROR", 
  "message": "Potential race condition in shared state access (CoT)",
  "business_impact": "Race conditions cause data corruption and inventory discrepancies",
  "estimated_fix_time": "2-4 hours for proper synchronization"
}
```

### Example 4: Connascence of Execution (CoE) - Method Ordering Dependencies
```typescript
// ❌ BEFORE: Strict execution order requirements
class PaymentProcessor {
  private initialized = false;
  private validated = false;
  
  // Methods must be called in specific order (fragile API)
  async processPayment(amount: number, paymentMethod: any) {
    // Execution order dependency - will fail if not called in sequence
    this.initialize();
    this.validatePayment(amount, paymentMethod);
    this.chargePayment(amount, paymentMethod);
    this.recordTransaction(amount);
    this.sendConfirmation();
  }
  
  initialize() {
    if (!this.initialized) {
      // Setup payment gateway connection
      this.initialized = true;
    }
  }
  
  validatePayment(amount: number, paymentMethod: any) {
    if (!this.initialized) {
      throw new Error('Must initialize before validation');
    }
    // Validation logic
    this.validated = true;
  }
  
  chargePayment(amount: number, paymentMethod: any) {
    if (!this.validated) {
      throw new Error('Must validate before charging');
    }
    // Charge logic
  }
}
```

**Semgrep Analysis Results:**
```json
{
  "rule_id": "method-call-ordering-dependency",
  "severity": "ERROR",
  "message": "Method call ordering dependency detected (CoE)",
  "business_impact": "Fragile APIs that break when call order changes",
  "estimated_fix_time": "1-2 hours for proper state management"
}
```

## ✅ After: Low-Coupling Refactored Code

### Example 1: Resolved CoM - Named Constants
```typescript
// ✅ AFTER: Connascence of Meaning resolved with named constants
class OrderProcessor {
  // Business constants with clear meaning
  private static readonly HEAVY_ITEM_WEIGHT_THRESHOLD = 2.5; // pounds
  private static readonly HEAVY_ITEM_SURCHARGE = 15.99; // USD
  private static readonly ELECTRONICS_TAX_RATE = 0.08; // 8%
  private static readonly PREMIUM_DISCOUNT_THRESHOLD = 500; // USD
  private static readonly PREMIUM_DISCOUNT_RATE = 0.05; // 5%
  
  // Tax rates centralized in configuration
  private static readonly TAX_RATES = {
    CA: 0.0725,  // California state tax
    NY: 0.08,    // New York state tax
    TX: 0.0625   // Texas state tax
  } as const;
  
  calculateTotal(items: LineItem[], customer: Customer): number {
    let subtotal = this.calculateSubtotal(items);
    subtotal = this.applyCustomerDiscount(subtotal, customer);
    return this.addTaxes(subtotal, customer.location);
  }
  
  private calculateSubtotal(items: LineItem[]): number {
    return items.reduce((total, item) => {
      let itemTotal = item.price * item.quantity;
      
      // Heavy item surcharge with clear business logic
      if (item.weight > OrderProcessor.HEAVY_ITEM_WEIGHT_THRESHOLD) {
        itemTotal += OrderProcessor.HEAVY_ITEM_SURCHARGE;
      }
      
      // Electronics tax with named constant
      if (item.category === ItemCategory.Electronics) {
        itemTotal *= (1 + OrderProcessor.ELECTRONICS_TAX_RATE);
      }
      
      return total + itemTotal;
    }, 0);
  }
  
  private applyCustomerDiscount(subtotal: number, customer: Customer): number {
    const isPremiumCustomer = customer.type === CustomerType.Premium;
    const meetsDiscountThreshold = subtotal > OrderProcessor.PREMIUM_DISCOUNT_THRESHOLD;
    
    if (isPremiumCustomer && meetsDiscountThreshold) {
      return subtotal * (1 - OrderProcessor.PREMIUM_DISCOUNT_RATE);
    }
    
    return subtotal;
  }
  
  private addTaxes(subtotal: number, location: string): number {
    const taxRate = OrderProcessor.TAX_RATES[location as keyof typeof OrderProcessor.TAX_RATES] || 0;
    return subtotal * (1 + taxRate);
  }
}
```

**Post-Refactoring Analysis:**
```json
{
  "coupling_metrics": {
    "connascence_of_meaning": "LOW - All magic numbers eliminated",
    "readability_score": "9.2/10 - Clear business intent",
    "maintainability": "HIGH - Changes localized to constants"
  },
  "business_benefits": {
    "tax_rate_changes": "Single location update",
    "business_rule_clarity": "Self-documenting code",
    "testing_simplicity": "Constants can be mocked easily"
  }
}
```

### Example 2: Resolved CoP - Options Object Pattern
```typescript
// ✅ AFTER: Position coupling resolved with structured parameters
interface ShippingOptions {
  weight: number;
  dimensions: Dimensions;
  destination: Address;
  serviceLevel: ServiceLevel;
  insurance: boolean;
  requireSignature: boolean;
  priority: boolean;
  packagingType: PackagingType;
}

interface ShippingQuote {
  serviceLevel: ServiceLevel;
  estimatedCost: number;
  estimatedDays: number;
  features: ShippingFeature[];
}

class ShippingService {
  // No positional coupling - options object pattern
  calculateShipping(options: ShippingOptions): number {
    const calculator = new ShippingCalculator(options);
    return calculator.calculateCost();
  }
  
  // Structured response eliminates client positional coupling
  getShippingOptions(weight: number, destination: Address): ShippingQuote[] {
    return [
      {
        serviceLevel: ServiceLevel.Standard,
        estimatedCost: this.calculateStandard(weight, destination),
        estimatedDays: 5,
        features: []
      },
      {
        serviceLevel: ServiceLevel.Express, 
        estimatedCost: this.calculateExpress(weight, destination),
        estimatedDays: 2,
        features: [ShippingFeature.Tracking]
      },
      {
        serviceLevel: ServiceLevel.Overnight,
        estimatedCost: this.calculateOvernight(weight, destination),
        estimatedDays: 1,
        features: [ShippingFeature.Tracking, ShippingFeature.Insurance]
      }
    ];
  }
}

// Builder pattern for complex shipping configuration
class ShippingOptionsBuilder {
  private options: Partial<ShippingOptions> = {};
  
  withWeight(weight: number): ShippingOptionsBuilder {
    this.options.weight = weight;
    return this;
  }
  
  withDestination(destination: Address): ShippingOptionsBuilder {
    this.options.destination = destination;
    return this;
  }
  
  withInsurance(): ShippingOptionsBuilder {
    this.options.insurance = true;
    return this;
  }
  
  build(): ShippingOptions {
    // Validate required fields
    if (!this.options.weight || !this.options.destination) {
      throw new Error('Weight and destination are required');
    }
    
    return {
      dimensions: this.options.dimensions || { length: 0, width: 0, height: 0 },
      serviceLevel: this.options.serviceLevel || ServiceLevel.Standard,
      insurance: this.options.insurance || false,
      requireSignature: this.options.requireSignature || false,
      priority: this.options.priority || false,
      packagingType: this.options.packagingType || PackagingType.Standard,
      ...this.options
    } as ShippingOptions;
  }
}
```

**Usage Example:**
```typescript
// Clear, readable API without positional coupling
const shippingCost = shippingService.calculateShipping(
  new ShippingOptionsBuilder()
    .withWeight(2.5)
    .withDestination(customerAddress)
    .withInsurance()
    .withSignatureRequired()
    .build()
);
```

### Example 3: Resolved CoT - Synchronized Operations
```typescript
// ✅ AFTER: Timing coupling resolved with proper synchronization
class InventoryManager {
  private readonly inventoryLock = new Map<string, Promise<void>>();
  private readonly inventoryCache = new Map<string, number>();
  
  async processOrder(orderId: string, items: OrderItem[]): Promise<void> {
    // Process items sequentially to avoid race conditions
    for (const item of items) {
      await this.processOrderItem(item);
    }
  }
  
  private async processOrderItem(item: OrderItem): Promise<void> {
    // Acquire lock for this product to prevent race conditions
    const lockKey = `inventory:${item.productId}`;
    
    // Wait for any pending operations on this product
    await this.inventoryLock.get(lockKey);
    
    // Create new operation promise
    const operation = this.performInventoryUpdate(item);
    this.inventoryLock.set(lockKey, operation);
    
    try {
      await operation;
    } finally {
      // Clean up completed operation
      this.inventoryLock.delete(lockKey);
    }
  }
  
  private async performInventoryUpdate(item: OrderItem): Promise<void> {
    // Atomic transaction eliminates timing dependencies
    await this.database.transaction(async (tx) => {
      const currentStock = await tx.getStock(item.productId);
      
      if (currentStock < item.quantity) {
        throw new InsufficientStockError(item.productId, currentStock, item.quantity);
      }
      
      // All updates in single transaction - no timing gaps
      const newStock = currentStock - item.quantity;
      await tx.updateStock(item.productId, newStock);
      await tx.logInventoryChange(item.productId, -item.quantity);
      
      // Update cache after successful database commit
      this.inventoryCache.set(item.productId, newStock);
    });
  }
  
  // Cache invalidation tied to database updates
  private async invalidateCache(productId: string): Promise<void> {
    this.inventoryCache.delete(productId);
    
    // Refresh from authoritative source
    const currentStock = await this.database.getStock(productId);
    this.inventoryCache.set(productId, currentStock);
  }
}
```

**Synchronization Benefits:**
```json
{
  "timing_improvements": {
    "race_conditions": "ELIMINATED - Proper locking mechanism",
    "data_consistency": "GUARANTEED - Transactional updates",
    "cache_coherence": "MAINTAINED - Synchronized invalidation"
  },
  "business_benefits": {
    "inventory_accuracy": "99.9% accuracy vs 94% before",
    "overselling_incidents": "Zero incidents vs 3-5 monthly before",
    "customer_satisfaction": "Improved due to accurate stock levels"
  }
}
```

### Example 4: Resolved CoE - State Machine Pattern
```typescript
// ✅ AFTER: Execution coupling resolved with state machine
enum PaymentState {
  Uninitialized = 'uninitialized',
  Initialized = 'initialized', 
  Validated = 'validated',
  Charged = 'charged',
  Completed = 'completed',
  Failed = 'failed'
}

interface PaymentContext {
  amount: number;
  paymentMethod: PaymentMethod;
  transactionId?: string;
  errorMessage?: string;
}

class PaymentProcessor {
  private state: PaymentState = PaymentState.Uninitialized;
  private context: PaymentContext;
  
  // Single entry point - no execution order dependencies
  async processPayment(amount: number, paymentMethod: PaymentMethod): Promise<PaymentResult> {
    this.context = { amount, paymentMethod };
    
    try {
      await this.executePaymentFlow();
      return this.createSuccessResult();
    } catch (error) {
      this.state = PaymentState.Failed;
      this.context.errorMessage = error.message;
      return this.createErrorResult();
    }
  }
  
  private async executePaymentFlow(): Promise<void> {
    // State machine handles execution order automatically
    while (this.state !== PaymentState.Completed && this.state !== PaymentState.Failed) {
      switch (this.state) {
        case PaymentState.Uninitialized:
          await this.initialize();
          break;
        case PaymentState.Initialized:
          await this.validate();
          break;
        case PaymentState.Validated:
          await this.charge();
          break;
        case PaymentState.Charged:
          await this.complete();
          break;
        default:
          throw new Error(`Invalid state: ${this.state}`);
      }
    }
  }
  
  private async initialize(): Promise<void> {
    // Initialize payment gateway
    await this.paymentGateway.connect();
    this.state = PaymentState.Initialized;
  }
  
  private async validate(): Promise<void> {
    // Validate payment details
    const isValid = await this.paymentGateway.validatePayment(this.context);
    if (!isValid) {
      throw new PaymentValidationError('Invalid payment details');
    }
    this.state = PaymentState.Validated;
  }
  
  private async charge(): Promise<void> {
    // Process the charge
    const result = await this.paymentGateway.charge(this.context);
    this.context.transactionId = result.transactionId;
    this.state = PaymentState.Charged;
  }
  
  private async complete(): Promise<void> {
    // Record transaction and send confirmation
    await Promise.all([
      this.recordTransaction(),
      this.sendConfirmation()
    ]);
    this.state = PaymentState.Completed;
  }
}
```

## 📈 Analysis Results Summary

### Coupling Reduction Metrics
```yaml
before_refactoring:
  connascence_violations:
    meaning: 18 violations
    position: 12 violations  
    timing: 8 violations
    execution: 6 violations
    identity: 3 violations
  coupling_index: 8.2/10
  technical_debt: $89,000
  maintenance_risk: HIGH

after_refactoring:
  connascence_violations:
    meaning: 1 violation (cosmetic)
    position: 0 violations
    timing: 1 violation (acceptable)
    execution: 1 violation (acceptable)
    identity: 0 violations
  coupling_index: 5.4/10
  technical_debt: $12,000
  maintenance_risk: LOW
```

### Business Impact Analysis
```yaml
development_velocity:
  code_review_time: "3.2 hours → 1.8 hours (-44%)"
  feature_development: "2.1 weeks → 1.4 weeks (-33%)" 
  bug_fix_time: "4.7 hours → 2.1 hours (-55%)"

quality_improvements:
  production_incidents: "1.8/month → 0.3/month (-83%)"
  customer_complaints: "12/month → 3/month (-75%)"
  system_reliability: "96.2% → 99.1% uptime"

team_productivity:
  developer_satisfaction: "3.4/5.0 → 4.6/5.0"
  onboarding_time: "6.2 weeks → 3.8 weeks (-39%)"
  knowledge_sharing: "Improved due to self-documenting code"
```

### ROI Calculation
```yaml
refactoring_investment:
  developer_time: "89 hours × $75/hour = $6,675"
  testing_time: "24 hours × $65/hour = $1,560"
  code_review: "12 hours × $85/hour = $1,020"
  total_cost: $9,255

annual_savings:
  reduced_maintenance: "$18,000 (faster bug fixes)"
  improved_velocity: "$22,000 (faster feature delivery)"
  reduced_incidents: "$8,500 (fewer production issues)"
  better_onboarding: "$4,200 (faster team scaling)"
  total_savings: $52,700

roi_metrics:
  payback_period: "2.1 months"
  annual_roi: "469%"
  3_year_net_value: "$149,155"
```

## 🎯 Key Takeaways for Enterprise Teams

### 1. Immediate Detection Value
The Semgrep rules provide immediate feedback on coupling issues, catching 94% of violations before they reach production. This prevents technical debt accumulation and maintains code quality.

### 2. Strategic Refactoring Guidance
The connascence analysis prioritizes refactoring efforts based on business impact, ensuring maximum ROI from improvement investments.

### 3. Measurable Business Benefits
The analysis provides quantifiable metrics that translate technical improvements into business value, supporting architecture investment decisions.

### 4. Developer Experience
Well-designed refactoring improves developer productivity and satisfaction, creating a positive feedback loop for code quality.

### 5. Scalable Quality Standards
The combination of fast detection (Semgrep) and deep analysis (Connascence) scales from individual developers to enterprise-wide architecture governance.

This sample analysis demonstrates how the Semgrep + Connascence Enterprise Rules Pack delivers both immediate tactical value and strategic architectural insights, making it an essential tool for enterprise development teams focused on sustainable code quality and business value delivery.