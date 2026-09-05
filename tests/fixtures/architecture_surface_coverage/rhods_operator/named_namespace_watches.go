package auth

// Sanitized source shape for literal, predicate-constrained Namespace watches.
func (h *ServiceHandler) NewReconciler(ctx context.Context, mgr ctrl.Manager) error {
	_, err := reconciler.ReconcilerFor(mgr, &serviceapi.Auth{}).
		Watches(
			&corev1.Namespace{},
			reconciler.WithEventHandler(handlers.ToNamed(serviceapi.AuthInstanceName)),
			reconciler.WithPredicates(
				resources.CreatedOrUpdatedOrDeletedNamed("models-as-a-service"),
			),
		).
		Watches(
			&corev1.Namespace{},
			reconciler.WithEventHandler(handlers.ToNamed(serviceapi.AuthInstanceName)),
			reconciler.WithPredicates(
				resources.CreatedOrUpdatedOrDeletedNamed("kuadrant-system"),
			),
		).
		Build(ctx)
	return err
}
